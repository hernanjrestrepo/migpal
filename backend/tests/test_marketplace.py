from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_housing_rentals_not_found():
    r = client.get("/api/v1/housing/rentals", params={"city": "Nowhere", "state": "ZZ"})
    assert r.status_code == 404


def test_marketplace_businesses_not_found():
    r = client.get("/api/v1/marketplace/businesses", params={"state": "TX"})
    assert r.status_code == 404
