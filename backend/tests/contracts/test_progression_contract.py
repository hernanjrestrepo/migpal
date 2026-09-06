"""
Contract tests: GET /v1/progression (Sprint 7, Hito 5).

Usa Ollama/Kimi real para assessment+recommendation (igual que
test_settlement_contract.py) porque el hito "ruta_elegida" depende de un
evento real de Recommendation.
"""

import uuid

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def _register_login_and_open_case() -> dict:
    suffix = uuid.uuid4().hex[:8]
    email = f"contract_prog_{suffix}@example.com"
    username = f"prog_{suffix}"
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


def test_progression_requires_auth():
    assert client.get("/v1/progression").status_code == 401


def test_fresh_case_starts_at_level_one_zero_xp():
    headers = _register_login_and_open_case()
    r = client.get("/v1/progression", headers=headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["xp"] == 0
    assert body["level"] == "Nivel 1 · Primeros pasos"
    assert all(not b["earned"] for b in body["badges"])


def test_calculating_budget_earns_xp_and_badge():
    headers = _register_login_and_open_case()

    client.post(
        "/v1/budget", headers=headers,
        json={
            "family_size": 3, "origin_monthly_income": 2200, "destination_monthly_income": 8700,
            "government_fee": 715, "relocation_cost_low": 6450, "relocation_cost_high": 10300,
            "settlement_cost": 31700,
        },
    )

    r = client.get("/v1/progression", headers=headers)
    body = r.json()
    assert body["xp"] == 30
    badge = next(b for b in body["badges"] if b["badge_id"] == "presupuesto_calculado")
    assert badge["earned"] is True


def test_full_settlement_checklist_earns_the_completion_badge():
    headers = _register_login_and_open_case()

    assessment = client.post(
        "/v1/assessment", headers=headers,
        json={
            "profile_text": (
                "Tengo 8 años de experiencia como ingeniero de software, maestría en "
                "ciencias de la computación, quiero migrar a Canadá, tengo esposa e hijo, "
                "y contamos con respaldo financiero suficiente."
            )
        },
    )
    assert assessment.status_code == 200, assessment.text

    recommendation = client.post("/v1/recommendation", headers=headers)
    assert recommendation.status_code == 200, recommendation.text
    rec_id = recommendation.json()["id"]
    accepted = client.post(f"/v1/recommendation/{rec_id}/accept", headers=headers)
    assert accepted.status_code == 200, accepted.text

    r = client.get("/v1/progression", headers=headers)
    ruta_badge = next(b for b in r.json()["badges"] if b["badge_id"] == "ruta_elegida")
    assert ruta_badge["earned"] is True
    assert r.json()["xp"] == 50 + 100  # evaluacion_completa + ruta_elegida

    checklist = client.post("/v1/settlement", headers=headers)
    assert checklist.status_code == 200, checklist.text

    r = client.get("/v1/progression", headers=headers)
    iniciados_badge = next(b for b in r.json()["badges"] if b["badge_id"] == "tramites_iniciados")
    assert iniciados_badge["earned"] is True
    completos_badge = next(b for b in r.json()["badges"] if b["badge_id"] == "tramites_completos")
    assert completos_badge["earned"] is False

    for item in checklist.json()["items"]:
        r2 = client.post(f"/v1/settlement/items/{item['id']}/status", headers=headers, json={"status": "DONE"})
        assert r2.status_code == 200, r2.text

    r = client.get("/v1/progression", headers=headers)
    body = r.json()
    completos_badge = next(b for b in body["badges"] if b["badge_id"] == "tramites_completos")
    assert completos_badge["earned"] is True
    assert body["xp"] == 50 + 100 + 20 + 100  # evaluacion + ruta_elegida + tramites_iniciados + tramites_completos


def test_community_post_earns_xp_regardless_of_case():
    headers = _register_login_and_open_case()
    group = client.post(
        "/v1/community/groups", headers=headers, json={"name": f"Grupo {uuid.uuid4().hex[:8]}"}
    ).json()
    client.post(f"/v1/community/groups/{group['id']}/posts", headers=headers, json={"body": "Hola"})

    r = client.get("/v1/progression", headers=headers)
    badge = next(b for b in r.json()["badges"] if b["badge_id"] == "comunidad_activa")
    assert badge["earned"] is True
