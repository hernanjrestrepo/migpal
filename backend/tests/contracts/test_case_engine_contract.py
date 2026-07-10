"""
Contract test: /v1/case, /v1/case/family-members (Anexo C).

Igual que test_identity_contract.py: contrato consumido por el frontend,
no lógica interna.
"""

import uuid

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

CASE_SCHEMA = {"id", "status", "objective_country", "objective_visa_type", "next_step_ref"}
FAMILY_MEMBER_SCHEMA = {"id", "full_name", "relationship_type"}


def _register_and_login() -> str:
    suffix = uuid.uuid4().hex[:8]
    email = f"contract_case_{suffix}@example.com"
    username = f"case_{suffix}"
    password = "Passw0rd!"

    r = client.post("/v1/auth/register", json={"email": email, "username": username, "password": password})
    assert r.status_code == 201, r.text

    token_resp = client.post(
        "/api/v1/auth/token",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert token_resp.status_code == 200, token_resp.text
    return token_resp.json()["access_token"]


def test_case_requires_authentication():
    response = client.get("/v1/case")
    assert response.status_code == 401


def test_open_case_status_and_schema():
    token = _register_and_login()
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/v1/case", headers=headers)

    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body.keys()) == CASE_SCHEMA, body.keys()
    assert body["status"] == "draft"
    assert body["objective_country"] is None


def test_open_case_is_idempotent():
    token = _register_and_login()
    headers = {"Authorization": f"Bearer {token}"}

    first = client.post("/v1/case", headers=headers).json()
    second = client.post("/v1/case", headers=headers).json()

    assert first["id"] == second["id"]


def test_update_objective_transitions_status_to_active():
    token = _register_and_login()
    headers = {"Authorization": f"Bearer {token}"}
    client.post("/v1/case", headers=headers)

    response = client.put(
        "/v1/case",
        headers=headers,
        json={"objective_country": "Canada", "objective_visa_type": "Express Entry"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body.keys()) == CASE_SCHEMA
    assert body["status"] == "active"
    assert body["objective_country"] == "Canada"


def test_update_objective_without_case_returns_404():
    # Usuario registrado pero SIN abrir case todavía.
    suffix = uuid.uuid4().hex[:8]
    email = f"contract_nocasef_{suffix}@example.com"
    username = f"nocase_{suffix}"
    client.post("/v1/auth/register", json={"email": email, "username": username, "password": "Passw0rd!"})
    token = client.post(
        "/api/v1/auth/token",
        data={"username": username, "password": "Passw0rd!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ).json()["access_token"]

    response = client.put(
        "/v1/case",
        headers={"Authorization": f"Bearer {token}"},
        json={"objective_country": "Espana"},
    )
    assert response.status_code == 404, response.text


def test_add_family_member_status_and_schema():
    token = _register_and_login()
    headers = {"Authorization": f"Bearer {token}"}
    client.post("/v1/case", headers=headers)

    response = client.post(
        "/v1/case/family-members",
        headers=headers,
        json={"full_name": "Ana Perez", "relationship_type": "child"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body.keys()) == FAMILY_MEMBER_SCHEMA, body.keys()
    assert body["full_name"] == "Ana Perez"
    assert body["relationship_type"] == "child"


def test_add_family_member_missing_field_returns_422():
    token = _register_and_login()
    headers = {"Authorization": f"Bearer {token}"}
    client.post("/v1/case", headers=headers)

    response = client.post("/v1/case/family-members", headers=headers, json={"full_name": "Sin tipo"})
    assert response.status_code == 422
