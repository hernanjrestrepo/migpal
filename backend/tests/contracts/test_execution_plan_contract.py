"""
Contract tests: POST /v1/execution-plan, GET /v1/execution-plan,
POST /v1/execution-plan/steps/{step_id}/complete (Sprint 3, Hito 4).

Llama a Ollama real (vía /v1/assessment y /v1/recommendation, igual que
tests/contracts/test_recommendation_contract.py) para armar una
Recommendation ACCEPTED real antes de poder generar el ExecutionPlan.
"""

import uuid

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

EXECUTION_PLAN_SCHEMA = {
    "id",
    "case_id",
    "recommendation_id",
    "status",
    "steps",
    "completed_count",
    "total_count",
}
PLAN_STEP_SCHEMA = {
    "id",
    "title",
    "description",
    "sequence",
    "status",
    "depends_on",
    "blocked",
    "blocked_by",
    "completed_at",
}


def _register_login_and_open_case() -> dict:
    suffix = uuid.uuid4().hex[:8]
    email = f"contract_plan_{suffix}@example.com"
    username = f"plan_{suffix}"
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


def _accepted_recommendation_headers() -> dict:
    headers = _register_login_and_open_case()

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

    recommendation = client.post("/v1/recommendation", headers=headers)
    assert recommendation.status_code == 200, recommendation.text

    accepted = client.post(f"/v1/recommendation/{recommendation.json()['id']}/accept", headers=headers)
    assert accepted.status_code == 200, accepted.text

    return headers


def test_execution_plan_requires_authentication():
    assert client.post("/v1/execution-plan").status_code == 401
    assert client.get("/v1/execution-plan").status_code == 401
    assert client.post("/v1/execution-plan/steps/1/complete").status_code == 401


def test_generar_execution_plan_without_accepted_recommendation_returns_404():
    headers = _register_login_and_open_case()
    assert client.post("/v1/execution-plan", headers=headers).status_code == 404


def test_get_execution_plan_before_generating_returns_404():
    headers = _register_login_and_open_case()
    assert client.get("/v1/execution-plan", headers=headers).status_code == 404


def test_complete_step_before_generating_plan_returns_404():
    headers = _register_login_and_open_case()
    assert client.post("/v1/execution-plan/steps/1/complete", headers=headers).status_code == 404


def test_full_flow_generate_read_and_complete_all_steps():
    headers = _accepted_recommendation_headers()

    created = client.post("/v1/execution-plan", headers=headers)
    assert created.status_code == 200, created.text
    body = created.json()
    assert set(body.keys()) == EXECUTION_PLAN_SCHEMA
    assert body["status"] == "ACTIVE"
    assert body["total_count"] >= 1
    assert body["completed_count"] == 0
    for step in body["steps"]:
        assert set(step.keys()) == PLAN_STEP_SCHEMA

    # El último paso (sequence más alta) depende de todos los demás -- está
    # bloqueado hasta completarlos (criterio de éxito 9, §12 del diseño).
    steps_by_sequence = sorted(body["steps"], key=lambda s: s["sequence"])
    final_step = steps_by_sequence[-1]
    document_steps = steps_by_sequence[:-1]
    assert final_step["blocked"] is True
    assert set(final_step["blocked_by"]) == {s["id"] for s in document_steps}

    read = client.get("/v1/execution-plan", headers=headers)
    assert read.status_code == 200, read.text
    assert read.json()["id"] == body["id"]

    # Completar el paso bloqueado se rechaza (invariante 3).
    blocked_attempt = client.post(f"/v1/execution-plan/steps/{final_step['id']}/complete", headers=headers)
    assert blocked_attempt.status_code == 409

    for step in document_steps:
        completed = client.post(f"/v1/execution-plan/steps/{step['id']}/complete", headers=headers)
        assert completed.status_code == 200, completed.text

    # Ya no está bloqueado -- todas sus dependencias se completaron.
    unblocked_view = client.get("/v1/execution-plan", headers=headers).json()
    unblocked_final = next(s for s in unblocked_view["steps"] if s["id"] == final_step["id"])
    assert unblocked_final["blocked"] is False

    completed_plan = client.post(f"/v1/execution-plan/steps/{final_step['id']}/complete", headers=headers)
    assert completed_plan.status_code == 200, completed_plan.text
    completed_body = completed_plan.json()
    assert completed_body["status"] == "COMPLETED"
    assert completed_body["completed_count"] == completed_body["total_count"]

    # El plan ya está COMPLETED -- terminal, no se le puede completar nada más.
    again = client.post(f"/v1/execution-plan/steps/{final_step['id']}/complete", headers=headers)
    assert again.status_code == 409


def test_generating_a_second_plan_while_one_is_active_returns_409():
    headers = _accepted_recommendation_headers()

    first = client.post("/v1/execution-plan", headers=headers)
    assert first.status_code == 200, first.text

    second = client.post("/v1/execution-plan", headers=headers)
    assert second.status_code == 409
