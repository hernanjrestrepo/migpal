"""
Contract tests: POST /v1/conversation/chat (Sprint 9, Hito 5).

Usa Kimi/Ollama real (según AI_PROVIDER) -- llamadas de verdad, no mocks.
Se mantiene modesto en cantidad porque "negocio" dispara 4 llamadas al
proveedor de IA en paralelo por test.
"""

import uuid

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def _register_login_and_open_case() -> dict:
    suffix = uuid.uuid4().hex[:8]
    email = f"contract_chat_{suffix}@example.com"
    username = f"chat_{suffix}"
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


def test_chat_requires_auth():
    assert client.post("/v1/conversation/chat", json={"context": "rutas", "message": "hola"}).status_code == 401


def test_chat_requires_an_open_case():
    suffix = uuid.uuid4().hex[:8]
    email = f"contract_chat_nocase_{suffix}@example.com"
    username = f"chatnc_{suffix}"
    client.post("/v1/auth/register", json={"email": email, "username": username, "password": "Passw0rd!"})
    token = client.post(
        "/api/v1/auth/token",
        data={"username": username, "password": "Passw0rd!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ).json()["access_token"]

    r = client.post(
        "/v1/conversation/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"context": "rutas", "message": "hola"},
    )
    assert r.status_code == 404


def test_single_specialist_context_replies_as_dany():
    headers = _register_login_and_open_case()
    r = client.post(
        "/v1/conversation/chat", headers=headers,
        json={"context": "rutas", "message": "¿Qué es la visa O-1A?"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body["replies"]) == 1
    assert body["replies"][0]["persona_id"] == "dany"
    assert body["replies"][0]["persona_name"] == "Dany"
    assert len(body["replies"][0]["text"]) > 0


def test_unknown_context_falls_back_to_angela():
    headers = _register_login_and_open_case()
    r = client.post(
        "/v1/conversation/chat", headers=headers,
        json={"context": "no_existe", "message": "hola"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["replies"][0]["persona_id"] == "angela"


def test_negocio_context_convenes_the_full_board():
    headers = _register_login_and_open_case()
    r = client.post(
        "/v1/conversation/chat", headers=headers,
        json={"context": "negocio", "message": "Quiero abrir una lavandería, ¿es viable?"},
    )
    assert r.status_code == 200, r.text
    persona_ids = {reply["persona_id"] for reply in r.json()["replies"]}
    assert persona_ids == {"tommy", "gabby", "ivan", "marcus"}
    assert all(len(reply["text"]) > 0 for reply in r.json()["replies"])
