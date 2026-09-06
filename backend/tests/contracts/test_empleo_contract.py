"""
Contract tests: POST /v1/empleo/connect, POST /v1/empleo/matches
(Sprint 10b, Hito 5).

Llama a JobXeeker real (`JOBXEEKER_BASE_URL`) -- se salta limpio si no
está corriendo, mismo criterio que test_negocio_contract.py con ADAN.
"""

import uuid

import httpx
import pytest
from fastapi.testclient import TestClient

from core.empleo.infrastructure.jobxeeker_client import JOBXEEKER_BASE_URL
from main import app

client = TestClient(app)


def _jobxeeker_is_up() -> bool:
    try:
        r = httpx.get(f"{JOBXEEKER_BASE_URL}/api/health/", timeout=3)
        return r.status_code < 500
    except httpx.HTTPError:
        return False


pytestmark = pytest.mark.skipif(not _jobxeeker_is_up(), reason=f"JobXeeker no está corriendo en {JOBXEEKER_BASE_URL}")


def _register_login_and_open_case() -> dict:
    suffix = uuid.uuid4().hex[:8]
    email = f"contract_empleo_{suffix}@example.com"
    username = f"empleo_{suffix}"
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


def test_empleo_endpoints_require_auth():
    assert client.post("/v1/empleo/connect", json={"name": "x"}).status_code == 401


def test_matches_before_connecting_returns_404():
    headers = _register_login_and_open_case()
    r = client.post("/v1/empleo/matches", headers=headers)
    assert r.status_code == 404


def test_connect_then_search_matches_end_to_end():
    headers = _register_login_and_open_case()

    connect = client.post(
        "/v1/empleo/connect", headers=headers,
        json={
            "name": "Camilo Restrepo",
            "target_roles": ["Senior Backend Engineer"],
            "target_industries": ["Technology"],
            "location_preference": "Austin, TX",
            "experience_level": "senior",
            "skills": ["Python", "FastAPI", "PostgreSQL"],
        },
    )
    assert connect.status_code == 200, connect.text
    assert connect.json()["jobxeeker_user_id"]

    connect_again = client.post("/v1/empleo/connect", headers=headers, json={"name": "otra vez"})
    assert connect_again.status_code == 409

    matches = client.post("/v1/empleo/matches", headers=headers)
    assert matches.status_code == 200, matches.text
    body = matches.json()
    # No se afirma que el matching tenga éxito -- JobXeeker puede estar en
    # degraded_mode (bug real encontrado del lado de JobXeeker, ver
    # jobxeeker_client.py). Se afirma que la respuesta es coherente.
    assert isinstance(body["matching_disponible"], bool)
    assert isinstance(body["matches"], list)
    if not body["matching_disponible"]:
        assert body["mensaje"]
