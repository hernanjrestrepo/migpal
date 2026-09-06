"""
Contract tests: /v1/marketplace/* (Sprint 6, Hito 5).

No depende de Ollama/Kimi.
"""

import uuid

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def _register_and_login(prefix: str) -> dict:
    suffix = uuid.uuid4().hex[:8]
    email = f"{prefix}_{suffix}@example.com"
    username = f"{prefix}_{suffix}"
    password = "Passw0rd!"

    r = client.post("/v1/auth/register", json={"email": email, "username": username, "password": password})
    assert r.status_code == 201, r.text

    token = client.post(
        "/api/v1/auth/token",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_listing(headers: dict, **overrides) -> dict:
    payload = {
        "category": "PLOMERIA", "title": "Reparación de calentadores", "price_amount": 45.0,
        "price_unit": "hora", "city": "Austin",
    }
    payload.update(overrides)
    r = client.post("/v1/marketplace/listings", headers=headers, json=payload)
    assert r.status_code == 200, r.text
    return r.json()


def test_marketplace_endpoints_require_auth():
    assert client.post("/v1/marketplace/listings", json={}).status_code == 401
    assert client.get("/v1/marketplace/listings").status_code == 401


def test_categories_include_childcare_and_disclaimer():
    r = client.get("/v1/marketplace/categories")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "CUIDADO_INFANTIL" in body["categories"]
    assert "intermediario" in body["disclaimer"].lower()
    assert "agencia" in body["disclaimer"].lower()


def test_listing_response_carries_the_disclaimer():
    headers = _register_and_login("mkt_seller")
    listing = _create_listing(headers, category="CUIDADO_INFANTIL", title="Niñera de confianza", price_unit="hora")
    assert listing["category"] == "CUIDADO_INFANTIL"
    assert "intermediario" in listing["disclaimer"].lower()


def test_full_transaction_lifecycle_computes_commission():
    seller = _register_and_login("mkt_seller2")
    buyer = _register_and_login("mkt_buyer2")
    listing = _create_listing(seller)

    r = client.post(
        "/v1/marketplace/transactions", headers=buyer,
        json={"listing_id": listing["id"], "amount": 100.0, "commission_rate": 0.08},
    )
    assert r.status_code == 200, r.text
    transaction = r.json()
    assert abs(transaction["commission_amount"] - 8.0) < 1e-6
    assert transaction["status"] == "PENDING"

    r = client.post(f"/v1/marketplace/transactions/{transaction['id']}/complete", headers=seller)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "COMPLETED"

    r = client.post(f"/v1/marketplace/transactions/{transaction['id']}/complete", headers=seller)
    assert r.status_code == 409


def test_cannot_buy_your_own_listing():
    seller = _register_and_login("mkt_seller3")
    listing = _create_listing(seller)

    r = client.post(
        "/v1/marketplace/transactions", headers=seller, json={"listing_id": listing["id"], "amount": 50.0}
    )
    assert r.status_code == 409


def test_transaction_not_visible_to_uninvolved_user():
    seller = _register_and_login("mkt_seller4")
    buyer = _register_and_login("mkt_buyer4")
    stranger = _register_and_login("mkt_stranger4")
    listing = _create_listing(seller)
    transaction = client.post(
        "/v1/marketplace/transactions", headers=buyer, json={"listing_id": listing["id"], "amount": 50.0}
    ).json()

    r = client.post(f"/v1/marketplace/transactions/{transaction['id']}/cancel", headers=stranger)
    assert r.status_code == 404


def test_cancel_pending_transaction():
    seller = _register_and_login("mkt_seller5")
    buyer = _register_and_login("mkt_buyer5")
    listing = _create_listing(seller)
    transaction = client.post(
        "/v1/marketplace/transactions", headers=buyer, json={"listing_id": listing["id"], "amount": 50.0}
    ).json()

    r = client.post(f"/v1/marketplace/transactions/{transaction['id']}/cancel", headers=buyer)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "CANCELLED"


def test_list_listings_filters_by_category():
    headers = _register_and_login("mkt_lister")
    _create_listing(headers, category="ELECTRICIDAD", title="Reparaciones eléctricas")

    r = client.get("/v1/marketplace/listings", headers=headers, params={"category": "ELECTRICIDAD"})
    assert r.status_code == 200, r.text
    assert all(item["category"] == "ELECTRICIDAD" for item in r.json())
