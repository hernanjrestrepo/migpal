"""
Contract tests: POST /v1/budget, GET /v1/budget (Sprint 1, Hito 5).

No depende de Ollama/Kimi -- Budget es cálculo determinístico puro, no
necesita ninguna Recommendation previa (a diferencia de ExecutionPlan).
"""

import uuid

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

BUDGET_SCHEMA = {
    "id",
    "case_id",
    "family_size",
    "migpal_service_fee",
    "government_fee",
    "relocation_cost_low",
    "relocation_cost_high",
    "settlement_cost",
    "legal_fee_low",
    "legal_fee_high",
    "total_low",
    "total_high",
    "origin_monthly_income",
    "destination_monthly_income",
    "monthly_differential",
    "breakeven_months",
}

VALID_PAYLOAD = {
    "family_size": 3,
    "origin_monthly_income": 2200,
    "destination_monthly_income": 8700,
    "government_fee": 715,
    "relocation_cost_low": 6450,
    "relocation_cost_high": 10300,
    "settlement_cost": 31700,
    "legal_fee_low": 2500,
    "legal_fee_high": 5000,
}


def _register_login_and_open_case() -> dict:
    suffix = uuid.uuid4().hex[:8]
    email = f"contract_budget_{suffix}@example.com"
    username = f"budget_{suffix}"
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


def test_budget_endpoints_require_auth():
    assert client.post("/v1/budget", json=VALID_PAYLOAD).status_code == 401
    assert client.get("/v1/budget").status_code == 401


def test_get_budget_before_calculating_returns_404():
    headers = _register_login_and_open_case()
    r = client.get("/v1/budget", headers=headers)
    assert r.status_code == 404


def test_post_budget_returns_schema_with_computed_totals_and_breakeven():
    headers = _register_login_and_open_case()

    r = client.post("/v1/budget", headers=headers, json=VALID_PAYLOAD)
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body.keys()) == BUDGET_SCHEMA
    assert body["migpal_service_fee"] == 1000.0
    assert body["total_low"] == 1000 + 715 + 6450 + 31700 + 2500
    assert body["total_high"] == 1000 + 715 + 10300 + 31700 + 5000
    assert body["monthly_differential"] == 6500
    assert body["breakeven_months"] > 0


def test_post_budget_charges_extra_per_person_beyond_five():
    headers = _register_login_and_open_case()
    payload = {**VALID_PAYLOAD, "family_size": 7}

    r = client.post("/v1/budget", headers=headers, json=payload)
    assert r.status_code == 200, r.text
    assert r.json()["migpal_service_fee"] == 1000.0 + 2 * 200.0


def test_post_budget_rejects_inverted_relocation_range():
    headers = _register_login_and_open_case()
    payload = {**VALID_PAYLOAD, "relocation_cost_low": 99999, "relocation_cost_high": 1}

    r = client.post("/v1/budget", headers=headers, json=payload)
    assert r.status_code == 400


def test_get_budget_returns_most_recent_calculation():
    headers = _register_login_and_open_case()
    client.post("/v1/budget", headers=headers, json=VALID_PAYLOAD)
    client.post("/v1/budget", headers=headers, json={**VALID_PAYLOAD, "family_size": 6})

    r = client.get("/v1/budget", headers=headers)
    assert r.status_code == 200, r.text
    assert r.json()["family_size"] == 6


# ---- Sprint 3: cotizador de traslado y comparación de remesas ----

RELOCATION_PAYLOAD = {
    "family_size": 3,
    "mode": "AEREO",
    "flight_cost_per_person_low": 1000,
    "flight_cost_per_person_high": 1300,
    "base_cargo_cost_low": 2800,
    "base_cargo_cost_high": 5500,
}


def test_relocation_estimate_requires_auth():
    assert client.post("/v1/budget/relocation-estimate", json=RELOCATION_PAYLOAD).status_code == 401


def test_relocation_estimate_returns_totals():
    headers = _register_login_and_open_case()
    r = client.post("/v1/budget/relocation-estimate", headers=headers, json=RELOCATION_PAYLOAD)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["flight_cost_low"] == 3000
    assert body["total_low"] > 0 and body["total_high"] > body["total_low"]


def test_relocation_estimate_rejects_invalid_range():
    headers = _register_login_and_open_case()
    payload = {**RELOCATION_PAYLOAD, "flight_cost_per_person_low": 9999, "flight_cost_per_person_high": 1}
    r = client.post("/v1/budget/relocation-estimate", headers=headers, json=payload)
    assert r.status_code == 400


REMITTANCE_PAYLOAD = {
    "amount": 500,
    "quotes": [
        {"provider_name": "Western Union", "fee": 8.0, "spread_percent": 3.5},
        {"provider_name": "Wise", "fee": 4.2, "spread_percent": 0},
    ],
}


def test_remittance_estimate_requires_auth():
    assert client.post("/v1/budget/remittance-estimate", json=REMITTANCE_PAYLOAD).status_code == 401


def test_remittance_estimate_sorts_best_option_first():
    headers = _register_login_and_open_case()
    r = client.post("/v1/budget/remittance-estimate", headers=headers, json=REMITTANCE_PAYLOAD)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body[0]["provider_name"] == "Wise"
    assert body[0]["amount_received"] > body[1]["amount_received"]
