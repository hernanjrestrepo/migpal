"""
Contract test: POST /v1/auth/register (Anexo C).

No prueba lógica interna -- prueba el CONTRATO que el frontend va a
consumir: forma exacta de la respuesta, códigos de estado, validación de
entrada. Si esto se rompe, se rompe el frontend, no un detalle interno.
"""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

# `email_verified` y `verification_email_sent` se sumaron al incorporar la
# verificación de email. `verification_email_sent` informa si el correo
# llegó a salir (puede ser false si SMTP no está configurado) -- nunca
# expone el token, que solo viaja dentro del email.
EXPECTED_SUCCESS_SCHEMA = {"id", "email", "username", "email_verified", "verification_email_sent"}


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
    # Una cuenta recién creada nunca nace verificada.
    assert body["email_verified"] is False
    # El token de verificación no debe aparecer en la respuesta bajo ningún
    # nombre: solo existe dentro del email.
    assert "token" not in response.text.lower()


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
