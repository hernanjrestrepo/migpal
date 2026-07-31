"""
Contract tests: POST /v1/recommendation, GET /v1/recommendation,
POST /v1/recommendation/{id}/accept, POST /v1/recommendation/{id}/discard
(Sprint 5, Hito 3).

Llaman a Ollama real para `narrative_summary` (vía /v1/assessment y
/v1/recommendation) -- más lentas que un contract test típico, mismo
criterio que test_conversation_assessment_contract.py: si el AI Adapter de
Recommendation se rompe, debe fallar acá.
"""

import uuid

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

RECOMMENDATION_SCHEMA = {
    "id",
    "case_id",
    "assessment_id",
    "status",
    "primary_evaluation",
    "alternative_evaluations",
    "confidence",
    "rationale",
    "narrative_summary",
    "next_step",
    "decision_engine_version",
    "policy_version",
    "knowledge_version",
    "recommendation_version",
    "version",
}


def _register_login_open_case_and_assess() -> tuple[str, dict]:
    suffix = uuid.uuid4().hex[:8]
    email = f"contract_rec_{suffix}@example.com"
    username = f"rec_{suffix}"
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

    assessment = client.post(
        "/v1/assessment",
        headers=headers,
        json={
            "profile_text": (
                "Soy ingeniero de software con 6 años de experiencia, tengo maestría, "
                "quiero migrar a Canadá con mi esposa e hijos, tenemos algo de ahorro."
            )
        },
    )
    assert assessment.status_code == 200, assessment.text
    return token, headers


def test_recommendation_requires_authentication():
    assert client.post("/v1/recommendation").status_code == 401
    assert client.get("/v1/recommendation").status_code == 401


def test_request_recommendation_without_assessment_returns_404():
    suffix = uuid.uuid4().hex[:8]
    email = f"contract_norec_{suffix}@example.com"
    username = f"norec_{suffix}"
    password = "Passw0rd!"

    client.post("/v1/auth/register", json={"email": email, "username": username, "password": password})
    token = client.post(
        "/api/v1/auth/token",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    client.post("/v1/case", headers=headers)

    response = client.post("/v1/recommendation", headers=headers)
    assert response.status_code == 404


def test_full_flow_generate_read_and_accept():
    _, headers = _register_login_open_case_and_assess()

    created = client.post("/v1/recommendation", headers=headers)
    assert created.status_code == 200, created.text
    body = created.json()
    assert set(body.keys()) == RECOMMENDATION_SCHEMA
    assert body["status"] == "ISSUED"
    assert body["decision_engine_version"] == "1.0"
    assert body["policy_version"] == "1.0"
    assert body["knowledge_version"] == "1.0"
    assert body["recommendation_version"] == "1.0"
    assert 0.0 <= body["confidence"] <= 1.0
    assert body["primary_evaluation"]["route"]["visa_type"]
    assert isinstance(body["rationale"], list) and len(body["rationale"]) > 0
    assert body["narrative_summary"]
    assert body["next_step"]["title"]

    read = client.get("/v1/recommendation", headers=headers)
    assert read.status_code == 200, read.text
    assert read.json()["id"] == body["id"]

    accepted = client.post(f"/v1/recommendation/{body['id']}/accept", headers=headers)
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["status"] == "ACCEPTED"

    # Regenerar (nueva Recommendation, status ISSUED) y aceptarla debe
    # rechazarse con 409 -- invariante 6, una sola ACCEPTED por caso.
    regenerated = client.post("/v1/recommendation", headers=headers)
    assert regenerated.status_code == 200, regenerated.text
    conflict = client.post(f"/v1/recommendation/{regenerated.json()['id']}/accept", headers=headers)
    assert conflict.status_code == 409


def test_discard_recommendation():
    _, headers = _register_login_open_case_and_assess()

    created = client.post("/v1/recommendation", headers=headers)
    assert created.status_code == 200, created.text
    rec_id = created.json()["id"]

    discarded = client.post(f"/v1/recommendation/{rec_id}/discard", headers=headers)
    assert discarded.status_code == 200, discarded.text
    assert discarded.json()["status"] == "DISCARDED"

    # Ya no se puede volver a descartar (transición inválida desde DISCARDED).
    again = client.post(f"/v1/recommendation/{rec_id}/discard", headers=headers)
    assert again.status_code == 409


def test_get_recommendation_before_any_request_returns_404():
    suffix = uuid.uuid4().hex[:8]
    email = f"contract_noget_{suffix}@example.com"
    username = f"noget_{suffix}"
    password = "Passw0rd!"

    client.post("/v1/auth/register", json={"email": email, "username": username, "password": password})
    token = client.post(
        "/api/v1/auth/token",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    client.post("/v1/case", headers=headers)

    assert client.get("/v1/recommendation", headers=headers).status_code == 404
