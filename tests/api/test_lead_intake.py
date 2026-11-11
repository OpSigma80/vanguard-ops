import uuid
from fastapi.testclient import TestClient

import main


client = TestClient(main.app)


class FakeCursor:
    def __init__(self, leads=None, audit_logs=None):
        self.leads = leads if leads is not None else {}
        self.audit_logs = audit_logs if audit_logs is not None else set()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def execute(self, query, params=None):
        self.query = query
        self.params = params or ()
        if query.startswith("UPDATE leads"):
            self.leads[self.params[4]] = self.params[:4]
        elif query.startswith("DELETE FROM audit_logs"):
            self.audit_logs.discard(self.params[0])

    def fetchone(self):
        if "RETURNING id" in self.query:
            return (uuid.uuid4(),)
        if "SELECT id FROM leads" in self.query:
            lead_id = self.params[0]
            return (lead_id,) if lead_id in self.leads else None
        if "SELECT id FROM audit_logs" in self.query:
            log_id = self.params[0]
            return (log_id,) if log_id in self.audit_logs else None
        return None


class FakeConnection:
    def __init__(self, cursor=None):
        self.fake_cursor = cursor

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def cursor(self):
        return self.fake_cursor or FakeCursor()

    def commit(self):
        pass


def test_create_lead_success(monkeypatch):
    monkeypatch.setattr(main.psycopg, "connect", lambda _: FakeConnection())

    response = client.post(
        "/api/v1/lead-intake",
        json={
            "full_name": "Test User",
            "email": "test@example.com",
            "phone": "123456789",
            "source": "unit_test",
        },
    )

    assert response.status_code == 201
    assert response.json()["full_name"] == "Test User"
    assert uuid.UUID(response.json()["id"])


def test_create_lead_invalid_email():
    response = client.post(
        "/api/v1/lead-intake",
        json={"full_name": "Error", "email": "esto-no-es-un-email"},
    )
    assert response.status_code == 422


def test_delete_lead_invalid_uuid():
    response = client.delete("/api/v1/leads/not-a-uuid")
    assert response.status_code == 422


def test_delete_audit_log_not_found(monkeypatch):
    monkeypatch.setattr(main.psycopg, "connect", lambda _: FakeConnection())

    response = client.delete("/api/v1/audit-logs/999999")

    assert response.status_code == 404


def test_update_existing_lead(monkeypatch):
    lead_id = uuid.uuid4()
    leads = {lead_id: ("Old Name", "old@example.com", "555-000", "old_source")}
    cursor = FakeCursor(leads=leads)
    connection = FakeConnection(cursor)
    monkeypatch.setattr(main.psycopg, "connect", lambda _: connection)

    response = client.patch(
        f"/api/v1/leads/{lead_id}",
        json={
            "full_name": "Updated User",
            "email": "updated@example.com",
            "phone": "555-111",
            "source": "new_source",
        },
    )

    assert response.status_code == 200
    assert leads[lead_id] == (
        "Updated User",
        "updated@example.com",
        "555-111",
        "new_source",
    )


def test_delete_existing_audit_log(monkeypatch):
    audit_logs = {42}
    cursor = FakeCursor(audit_logs=audit_logs)
    connection = FakeConnection(cursor)
    monkeypatch.setattr(main.psycopg, "connect", lambda _: connection)

    response = client.delete("/api/v1/audit-logs/42")

    assert response.status_code == 200
    assert 42 not in audit_logs


def test_update_nonexistent_lead(monkeypatch):
    monkeypatch.setattr(main.psycopg, "connect", lambda _: FakeConnection())

    response = client.patch(
        f"/api/v1/leads/{uuid.uuid4()}",
        json={
            "full_name": "Missing User",
            "email": "missing@example.com",
            "phone": "555-222",
            "source": "unit_test",
        },
    )

    assert response.status_code == 404
