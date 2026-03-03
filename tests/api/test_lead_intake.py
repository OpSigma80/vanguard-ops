from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_lead_success():
    # Simulamos un envío de datos válido
    response = client.post(
        "/api/v1/lead-intake",
        json={
            "full_name": "Test User",
            "email": "test@example.com",
            "phone": "123456789",
            "source": "unit_test"
        }
    )
    assert response.status_code == 201
    assert response.json()["full_name"] == "Test User"
    assert "id" in response.json()

def test_create_lead_invalid_email():
    # Probamos el "Muro de Acero" con un email mal escrito
    response = client.post(
        "/api/v1/lead-intake",
        json={"full_name": "Error", "email": "esto-no-es-un-email"}
    )
    assert response.status_code == 422 # Error de validación automática