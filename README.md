# VanguardOps

VanguardOps is a lead-intake dashboard and API built with FastAPI, PostgreSQL, Jinja2, and Docker. It supports creating, listing, and deleting leads, records creation and deletion events in an audit log, and exposes interactive API documentation.

<img width="1312" height="610" alt="VanguardOps dashboard" src="https://github.com/user-attachments/assets/e477346d-fa2d-4a3d-af32-d4deb95877ea" />

## Features

Implemented application behavior:

- Lead dashboard rendered with Jinja2
- Lead creation, correction, and deletion from the dashboard and JSON API
- Email validation with Pydantic
- Lead deletion with UUID validation
- PostgreSQL persistence
- Automatic creation of required tables at application startup
- Creation and deletion audit records
- Dashboard totals for leads and distinct sources
- Docker Compose deployment
- Configurable CORS origins
- Swagger UI and OpenAPI documentation

Dashboard presentation values:

- `Total Leads` and the distinct-source count are read from PostgreSQL.
- `Nodes` represents the number of distinct lead sources, not application or infrastructure node count.
- The `Operational`, `ONLINE`, and `99.9%` status/uptime labels are static display values and are not populated by health checks, metrics, or uptime monitoring.

## URLs

- Dashboard: `http://localhost:8001`
- Swagger UI: `http://localhost:8001/docs`
- OpenAPI schema: `http://localhost:8001/openapi.json`

## Data persistence and memory

Leads and system audit logs are stored in PostgreSQL and persist across API
restarts, rather than existing only in FastAPI process memory.

- Leads created from the dashboard or API are saved in the `leads` table.
- Creation, update, and deletion actions are recorded in the `audit_logs` table.
- Dashboard leads are read from PostgreSQL each time the page is loaded.
- The dashboard shows the latest 10 leads and the latest 15 audit log entries.
- Docker Compose uses the `postgres_data` volume for database persistence.
- Refreshing or restarting the API does not delete the stored leads or logs.
- Individual audit-log entries can be deleted from the System Logs panel.

For normal operations:

- `docker compose down` stops the containers without deleting database data.
- Restart with `docker compose up -d`.
- Use `docker compose down -v` only if you intentionally want to delete all leads,
  audit logs, and other PostgreSQL data stored in the Docker volume.

PostgreSQL is the only durable application database. Browser memory is used only
for temporary form values while editing a lead.

## Technology

- Python 3.12
- FastAPI and Uvicorn
- Pydantic and EmailStr validation
- Psycopg 3
- PostgreSQL 17
- Jinja2
- Docker Compose
- pytest

## API

### Create a lead

```http
POST /api/v1/lead-intake
Content-Type: application/json

{
  "full_name": "Test User",
  "email": "test@example.com",
  "phone": "555-000",
  "source": "Cloud-Node"
}
```

Successful creation returns `201 Created`.

### Update a lead

```http
PATCH /api/v1/leads/{lead_id}
Content-Type: application/json

{
  "full_name": "Updated User",
  "email": "updated@example.com",
  "phone": "555-111",
  "source": "Dashboard V1"
}
```

Returns `200` after updating the lead, `404` when the lead does not exist, and `422` for a malformed UUID.

### Delete a lead

```http
DELETE /api/v1/leads/{lead_id}
```

Returns `200` after deletion, `404` when the lead does not exist, and `422` for a malformed UUID.

### Delete an individual System Log record

```http
DELETE /api/v1/audit-logs/{log_id}
```

Returns `200` after deletion and `404` when the audit log record does not exist.

## Run with Docker

1. Copy the environment template:

   ```powershell
   Copy-Item .env.example .env
   ```

2. Replace the example database password in `.env` and keep the container hostname `db` for Docker Compose:

   ```env
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=your-strong-password
   POSTGRES_DB=automation_engine_db
   DATABASE_URL=postgresql://postgres:your-strong-password@db:5432/automation_engine_db
   ```

The PostgreSQL hostname is `db` only when the API runs through Docker Compose. For a local API process that connects directly to a database exposed by Compose, use `localhost` instead. Compose also builds `DATABASE_URL` from `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB`; keep all values consistent.

3. Start the services:

   ```powershell
   docker compose up --build -d
   ```

4. Open `http://localhost:8001`.

Stop containers without deleting PostgreSQL data:

```powershell
docker compose down
```

Use `docker compose down -v` only when you intend to delete the database volume.

## Tests

Run the test suite inside the API container:

```powershell
docker compose exec api pytest -q
```

The suite currently verifies lead model normalization and validation, email validation, lead creation and updates, audit-log deletion, not-found responses, and malformed UUID handling.

Verified locally with Python 3.12.3: 9 tests passed with one pending deprecation warning from `python-multipart`.

Docker-based execution has not been verified as part of this README update.

## Project structure

```text
.
├── app/
│   ├── api/
│   ├── application/
│   ├── domain/
│   └── infrastructure/
├── templates/
├── tests/
├── Dockerfile
├── docker-compose.yml
├── main.py
└── requirements.txt
```

## Scope and roadmap

This is a functional portfolio application. Authentication, authorization, MFA, background workers, external CRM or email integrations, WebSocket telemetry, distributed caching, formal monitoring, backups, high availability, and SLA guarantees are not currently implemented.

## Limitations and data handling

- The API and dashboard do not implement authentication or authorization. Do not expose this application publicly without adding and validating an access-control layer.
- The dashboard and database store names, email addresses, phone numbers, source values, and audit details. Do not place personal or sensitive data in a public deployment unless collection, retention, access, encryption, and privacy requirements have been reviewed and implemented.
- Database startup and application behavior require a reachable PostgreSQL instance. Failures opening a connection are reported through the dashboard or API error responses.
- Existing automated tests cover selected unit and API paths. They do not verify PostgreSQL integration, dashboard rendering, deletion success, concurrent access, backups, authentication, or production availability.

Response time depends on workload and infrastructure; sub-100 ms performance is not claimed or guaranteed.
