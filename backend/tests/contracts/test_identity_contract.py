"""
Contract test: POST /v1/auth/register (Anexo C).

No prueba lógica interna -- prueba el CONTRATO que el frontend va a
consumir: forma exacta de la respuesta, códigos de estado, validación de
entrada. Si esto se rompe, se rompe el frontend, no un detalle interno.
"""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

EXPECTED_SUCCESS_SCHEMA = {"id", "email", "username"}


def _unique_email() -> str:
    import uuid

    return f"contract_{uuid.uuid4().hex[:8]}@example.com"


def test_register_success_status_and_schema():
    email = _unique_email()
    response = client.post(
        "/v1/auth/register",
        json={"email": email, "username": email.split("@")[0], "password": "Passw0rd!"},
    )

    assert response.status_code == 201, response.text
    body = response.json()

    assert set(body.keys()) == EXPECTED_SUCCESS_SCHEMA, body.keys()
    assert isinstance(body["id"], int)
    assert body["email"] == email
    assert isinstance(body["username"], str)


def test_register_duplicate_returns_409_not_500():
    email = _unique_email()
    payload = {"email": email, "username": email.split("@")[0], "password": "Passw0rd!"}

    first = client.post("/v1/auth/register", json=payload)
    assert first.status_code == 201

    second = client.post("/v1/auth/register", json=payload)
    assert second.status_code == 409, second.text
    assert "detail" in second.json()


def test_register_invalid_email_returns_422():
    response = client.post(
        "/v1/auth/register",
        json={"email": "no-es-un-email", "username": "x", "password": "Passw0rd!"},
    )
    assert response.status_code == 422


def test_register_missing_password_returns_422():
    response = client.post(
        "/v1/auth/register",
        json={"email": _unique_email(), "username": "sin_password"},
    )
    assert response.status_code == 422
