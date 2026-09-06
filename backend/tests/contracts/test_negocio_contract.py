"""
Contract tests: POST /v1/negocio/connect, POST /v1/negocio/board-room
(Sprint 10, Hito 5).

Llama a ADAN real (`ADAN_BASE_URL`, default http://localhost:8050) --
a diferencia de Kimi (siempre disponible para este repo), ADAN es un
tercer servicio externo que no siempre va a estar corriendo. Estos tests
se saltan limpio si no lo está, en vez de romper la suite completa de
MigPAL por la salud de otro repo.
"""

import uuid

import httpx
import pytest
from fastapi.testclient import TestClient

from core.negocio.infrastructure.adan_client import ADAN_BASE_URL
from main import app

client = TestClient(app)


def _adan_is_up() -> bool:
    try:
        r = httpx.get(f"{ADAN_BASE_URL}/health", timeout=3)
        return r.status_code == 200
    except httpx.HTTPError:
        return False


pytestmark = pytest.mark.skipif(not _adan_is_up(), reason=f"ADAN no está corriendo en {ADAN_BASE_URL}")


def _register_login_and_open_case() -> dict:
    suffix = uuid.uuid4().hex[:8]
    email = f"contract_negocio_{suffix}@example.com"
    username = f"negocio_{suffix}"
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


def test_negocio_endpoints_require_auth():
    assert client.post("/v1/negocio/connect", json={}).status_code == 401


def test_board_room_before_connecting_returns_404():
    headers = _register_login_and_open_case()
    r = client.post("/v1/negocio/board-room", headers=headers, json={"message": "hola"})
    assert r.status_code == 404


def test_connect_then_board_room_end_to_end():
    headers = _register_login_and_open_case()

    connect = client.post(
        "/v1/negocio/connect", headers=headers,
        json={
            "idea_name": f"Taller {uuid.uuid4().hex[:6]}",
            "idea_description": "Taller de reparación de bicicletas eléctricas para migrantes en Austin, "
                                 "presupuesto inicial de 15.000 dólares",
            "industry": "retail",
            "country": "Estados Unidos",
        },
    )
    assert connect.status_code == 200, connect.text
    assert connect.json()["adan_company_id"]

    connect_again = client.post(
        "/v1/negocio/connect", headers=headers,
        json={"idea_name": "otra idea", "idea_description": "otra"},
    )
    assert connect_again.status_code == 409

    board = client.post(
        "/v1/negocio/board-room", headers=headers,
        json={"message": "¿Es viable esta idea con ese presupuesto?"},
    )
    assert board.status_code == 200, board.text
    body = board.json()
    assert body["decision"] in {"PROCEED", "PIVOT", "STOP"}
    assert len(body["votes"]) > 0
