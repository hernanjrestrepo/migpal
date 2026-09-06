"""
Contract tests: POST /v1/settlement, GET /v1/settlement,
POST /v1/settlement/items/{item_id}/status (Sprint 2, Hito 5).

Llama a Ollama/Kimi real (vía /v1/assessment y /v1/recommendation, igual
que tests/contracts/test_execution_plan_contract.py) para armar una
Recommendation ACCEPTED real antes de poder generar el checklist.
"""

import uuid

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

CHECKLIST_SCHEMA = {"id", "case_id", "country", "items", "done_count", "total_count"}
ITEM_SCHEMA = {"id", "title", "description", "sequence", "status", "updated_at"}


def _register_login_and_open_case() -> dict:
    suffix = uuid.uuid4().hex[:8]
    email = f"contract_settlement_{suffix}@example.com"
    username = f"settle_{suffix}"
    password = "Passw0rd!"

    r = client.post("/v1/auth/register", json={"email": email, "username": username, "password": password})
    assert r.status_code == 201, r.text

    token = client.post(
        "/api/v1/auth/token",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    case_resp = client.post("/v1/case", headers=headers)
    assert case_resp.status_code == 200, case_resp.text
    return headers


def _accept_a_recommendation(headers: dict) -> None:
    """Mismo flujo que test_execution_plan_contract.py: assessment ->
    generar Recommendation -> aceptarla."""

    assessment = client.post(
        "/v1/assessment",
        headers=headers,
        json={
            "profile_text": (
                "Tengo 8 años de experiencia como ingeniero de software, maestría en "
                "ciencias de la computación, quiero migrar a Canadá, tengo esposa e hijo, "
                "y contamos con respaldo financiero suficiente."
            )
        },
    )
    assert assessment.status_code == 200, assessment.text

    rec = client.post("/v1/recommendation", headers=headers)
    assert rec.status_code == 200, rec.text
    rec_id = rec.json()["id"]
    accept = client.post(f"/v1/recommendation/{rec_id}/accept", headers=headers)
    assert accept.status_code == 200, accept.text


def test_settlement_endpoints_require_auth():
    assert client.post("/v1/settlement").status_code == 401
    assert client.get("/v1/settlement").status_code == 401


def test_get_settlement_before_generating_returns_404():
    headers = _register_login_and_open_case()
    r = client.get("/v1/settlement", headers=headers)
    assert r.status_code == 404


def test_post_settlement_without_accepted_recommendation_returns_404():
    headers = _register_login_and_open_case()
    r = client.post("/v1/settlement", headers=headers)
    assert r.status_code == 404


def test_post_settlement_generates_checklist_from_accepted_recommendation_country():
    headers = _register_login_and_open_case()
    _accept_a_recommendation(headers)

    r = client.post("/v1/settlement", headers=headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body.keys()) == CHECKLIST_SCHEMA
    assert body["total_count"] == 6
    assert body["done_count"] == 0
    assert set(body["items"][0].keys()) == ITEM_SCHEMA


def test_post_settlement_twice_returns_409():
    headers = _register_login_and_open_case()
    _accept_a_recommendation(headers)
    client.post("/v1/settlement", headers=headers)

    r = client.post("/v1/settlement", headers=headers)
    assert r.status_code == 409


def test_update_item_status_then_get_reflects_done_count():
    headers = _register_login_and_open_case()
    _accept_a_recommendation(headers)
    checklist = client.post("/v1/settlement", headers=headers).json()
    item_id = checklist["items"][0]["id"]

    r = client.post(f"/v1/settlement/items/{item_id}/status", headers=headers, json={"status": "DONE"})
    assert r.status_code == 200, r.text
    assert r.json()["done_count"] == 1

    r = client.get("/v1/settlement", headers=headers)
    assert r.json()["done_count"] == 1
