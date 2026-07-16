"""
Contract tests: POST /v1/messages, POST /v1/assessment, GET /v1/assessment
(Hito 2).

Llaman al Ollama real (no mockeado) -- son más lentas que un contract test
típico, pero es exactamente el punto: si el AI Adapter se rompe, esto debe
fallar aquí, no en producción. `score_profile_text` (Decision Engine) sí es
determinístico y se prueba aparte, sin red, en test_decision_engine_scoring.py.
"""

import uuid

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

ASSESSMENT_SCHEMA = {
    "id",
    "case_id",
    "score",
    "confidence",
    "findings",
    "recommendations",
    "decision_engine_version",
    "policy_version",
    "knowledge_version",
    "ai_reflection",
}


def _register_login_and_open_case() -> str:
    suffix = uuid.uuid4().hex[:8]
    email = f"contract_conv_{suffix}@example.com"
    username = f"conv_{suffix}"
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
    return token


def test_messages_requires_authentication():
    response = client.post("/v1/messages", json={"message": "hola"})
    assert response.status_code == 401


def test_send_message_status_and_schema():
    token = _register_login_and_open_case()
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/v1/messages", headers=headers, json={"message": "Hola, quiero migrar a Canada"})

    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body.keys()) == {"reply"}
    assert isinstance(body["reply"], str)
    assert len(body["reply"]) > 0


def test_request_assessment_status_and_full_schema_with_versions():
    token = _register_login_and_open_case()
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/v1/assessment",
        headers=headers,
        json={
            "profile_text": (
                "Soy ingeniero de software con 6 años de experiencia, tengo maestría, "
                "quiero migrar a Canada con mi esposa e hijos, tenemos algo de ahorro."
            )
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body.keys()) == ASSESSMENT_SCHEMA, body.keys()

    # Regla 4 -- las versiones deben existir SIEMPRE, aunque sean "1.0".
    assert body["decision_engine_version"] == "1.0"
    assert body["policy_version"] == "1.0"
    assert body["knowledge_version"] == "1.0"

    assert 0.0 <= body["score"] <= 100.0
    assert 0.0 <= body["confidence"] <= 1.0
    assert isinstance(body["findings"], list) and len(body["findings"]) > 0
    assert isinstance(body["recommendations"], list) and len(body["recommendations"]) > 0
    assert isinstance(body["ai_reflection"], str) and len(body["ai_reflection"]) > 0


def test_get_assessment_before_any_request_returns_404():
    token = _register_login_and_open_case()
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/v1/assessment", headers=headers)
    assert response.status_code == 404


def test_get_assessment_after_request_returns_the_persisted_one():
    token = _register_login_and_open_case()
    headers = {"Authorization": f"Bearer {token}"}

    created = client.post(
        "/v1/assessment", headers=headers, json={"profile_text": "Tengo experiencia y quiero ir a España."}
    ).json()

    read = client.get("/v1/assessment", headers=headers)
    assert read.status_code == 200, read.text
    body = read.json()
    assert body["id"] == created["id"]
    assert body["score"] == created["score"]
