"""
Contract tests: /v1/family-planning/* (Sprint 4, Hito 5).

No depende de Ollama/Kimi -- no necesita ninguna Recommendation previa.
"""

import uuid

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def _register_login_and_open_case() -> dict:
    suffix = uuid.uuid4().hex[:8]
    email = f"contract_fp_{suffix}@example.com"
    username = f"fp_{suffix}"
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


def test_family_planning_endpoints_require_auth():
    assert client.get("/v1/family-planning").status_code == 401
    assert client.post("/v1/family-planning/geography/country", json={"country": "x"}).status_code == 401


def test_get_family_planning_before_any_selection_is_empty_but_200():
    headers = _register_login_and_open_case()
    r = client.get("/v1/family-planning", headers=headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["country"] is None
    assert body["survey_total_count"] == 1  # solo el titular, sin encuestas respondidas todavía
    assert body["survey_completed_count"] == 0


def test_geography_cascade_enforces_order():
    headers = _register_login_and_open_case()

    r = client.post("/v1/family-planning/geography/state", headers=headers, json={"state": "Texas"})
    assert r.status_code == 400

    r = client.post("/v1/family-planning/geography/country", headers=headers, json={"country": "Estados Unidos"})
    assert r.status_code == 200, r.text

    r = client.post("/v1/family-planning/geography/state", headers=headers, json={"state": "Texas"})
    assert r.status_code == 200, r.text

    r = client.post("/v1/family-planning/geography/city", headers=headers, json={"city": "Austin"})
    assert r.status_code == 200, r.text

    r = client.post(
        "/v1/family-planning/geography/neighborhood", headers=headers, json={"neighborhood": "North Austin"}
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert (body["country"], body["state"], body["city"], body["neighborhood"]) == (
        "Estados Unidos", "Texas", "Austin", "North Austin",
    )


def test_changing_country_resets_lower_levels():
    headers = _register_login_and_open_case()
    client.post("/v1/family-planning/geography/country", headers=headers, json={"country": "Estados Unidos"})
    client.post("/v1/family-planning/geography/state", headers=headers, json={"state": "Texas"})

    client.post("/v1/family-planning/geography/country", headers=headers, json={"country": "Canadá"})

    r = client.get("/v1/family-planning", headers=headers)
    assert r.json()["state"] is None


def test_survey_primary_applicant_can_respond_once():
    headers = _register_login_and_open_case()
    payload = {"is_primary_applicant": True, "climate_preference": "cálido", "top_priority": "empleo"}

    r = client.post("/v1/family-planning/survey", headers=headers, json=payload)
    assert r.status_code == 200, r.text
    assert r.json()["survey_completed_count"] == 1

    r = client.post("/v1/family-planning/survey", headers=headers, json=payload)
    assert r.status_code == 400


def test_survey_for_unknown_family_member_returns_404():
    headers = _register_login_and_open_case()
    payload = {"case_family_member_id": 999999, "is_primary_applicant": False}
    r = client.post("/v1/family-planning/survey", headers=headers, json=payload)
    assert r.status_code == 404


def test_place_options_add_and_list():
    headers = _register_login_and_open_case()
    payload = {
        "option_type": "SCHOOL",
        "name": "Austin International School",
        "website": "https://example.com",
        "phone": "+1-512-555-0100",
        "requirements": "Prueba de nivel de inglés",
        "cost_amount": 9200,
        "cost_period": "anual",
    }

    r = client.post("/v1/family-planning/options", headers=headers, json=payload)
    assert r.status_code == 200, r.text
    assert r.json()["name"] == "Austin International School"

    r = client.get("/v1/family-planning/options", headers=headers, params={"option_type": "SCHOOL"})
    assert r.status_code == 200, r.text
    assert len(r.json()) == 1

    r = client.get("/v1/family-planning/options", headers=headers, params={"option_type": "HOUSING"})
    assert r.json() == []
