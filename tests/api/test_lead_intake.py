import uuid
from fastapi.testclient import TestClient

import main


client = TestClient(main.app)


class FakeCursor:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def execute(self, query, params=None):
        self.query = query

    def fetchone(self):
        if "RETURNING id" in self.query:
            return (uuid.uuid4(),)
        return None


class FakeConnection:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def cursor(self):
        return FakeCursor()

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
