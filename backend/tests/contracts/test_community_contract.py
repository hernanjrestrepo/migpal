"""
Contract tests: /v1/community/* (Sprint 5, Hito 5).

No depende de Ollama/Kimi ni de un MigrationCase -- Community es
independiente del caso migratorio de cada usuario.
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


def _create_group(headers: dict) -> dict:
    name = f"Grupo de prueba {uuid.uuid4().hex[:8]}"
    r = client.post(
        "/v1/community/groups", headers=headers,
        json={"name": name, "description": "Grupo de prueba", "city": "Austin", "country": "Estados Unidos"},
    )
    assert r.status_code == 200, r.text
    return r.json()


def test_community_endpoints_require_auth():
    assert client.get("/v1/community/groups").status_code == 401
    assert client.post("/v1/community/groups", json={"name": "x"}).status_code == 401


def test_creating_a_group_auto_joins_the_creator():
    headers = _register_and_login("comm_creator")
    group = _create_group(headers)
    assert group["is_member"] is True
    assert group["member_count"] == 1


def test_creator_can_post_without_a_separate_join_call():
    headers = _register_and_login("comm_poster")
    group = _create_group(headers)

    r = client.post(f"/v1/community/groups/{group['id']}/posts", headers=headers, json={"body": "Hola a todos"})
    assert r.status_code == 200, r.text
    assert r.json()["body"] == "Hola a todos"
    assert r.json()["like_count"] == 0


def test_non_member_cannot_post_but_can_after_joining():
    creator = _register_and_login("comm_owner")
    group = _create_group(creator)
    other = _register_and_login("comm_other")

    r = client.post(f"/v1/community/groups/{group['id']}/posts", headers=other, json={"body": "intento sin unirme"})
    assert r.status_code == 409

    join = client.post(f"/v1/community/groups/{group['id']}/join", headers=other)
    assert join.status_code == 200, join.text
    assert join.json()["member_count"] == 2

    r = client.post(f"/v1/community/groups/{group['id']}/posts", headers=other, json={"body": "ya soy miembro"})
    assert r.status_code == 200, r.text


def test_joining_twice_returns_409():
    creator = _register_and_login("comm_owner2")
    group = _create_group(creator)
    other = _register_and_login("comm_other2")
    client.post(f"/v1/community/groups/{group['id']}/join", headers=other)

    r = client.post(f"/v1/community/groups/{group['id']}/join", headers=other)
    assert r.status_code == 409


def test_comment_requires_membership():
    creator = _register_and_login("comm_owner3")
    group = _create_group(creator)
    post = client.post(
        f"/v1/community/groups/{group['id']}/posts", headers=creator, json={"body": "post original"}
    ).json()

    other = _register_and_login("comm_other3")
    r = client.post(f"/v1/community/posts/{post['id']}/comments", headers=other, json={"body": "sin ser miembro"})
    assert r.status_code == 409

    client.post(f"/v1/community/groups/{group['id']}/join", headers=other)
    r = client.post(f"/v1/community/posts/{post['id']}/comments", headers=other, json={"body": "ahora sí"})
    assert r.status_code == 200, r.text


def test_like_then_unlike_updates_counts_and_prevents_double_like():
    creator = _register_and_login("comm_owner4")
    group = _create_group(creator)
    post = client.post(
        f"/v1/community/groups/{group['id']}/posts", headers=creator, json={"body": "post para likear"}
    ).json()

    r = client.post(f"/v1/community/posts/{post['id']}/like", headers=creator)
    assert r.status_code == 200, r.text
    assert r.json()["like_count"] == 1
    assert r.json()["liked_by_me"] is True

    r = client.post(f"/v1/community/posts/{post['id']}/like", headers=creator)
    assert r.status_code == 409

    r = client.request("DELETE", f"/v1/community/posts/{post['id']}/like", headers=creator)
    assert r.status_code == 200, r.text
    assert r.json()["like_count"] == 0
    assert r.json()["liked_by_me"] is False

    r = client.request("DELETE", f"/v1/community/posts/{post['id']}/like", headers=creator)
    assert r.status_code == 409


def test_list_groups_and_posts():
    headers = _register_and_login("comm_lister")
    group = _create_group(headers)
    client.post(f"/v1/community/groups/{group['id']}/posts", headers=headers, json={"body": "primer post"})

    groups = client.get("/v1/community/groups", headers=headers)
    assert groups.status_code == 200
    assert any(g["id"] == group["id"] for g in groups.json())

    posts = client.get(f"/v1/community/groups/{group['id']}/posts", headers=headers)
    assert posts.status_code == 200
    assert len(posts.json()) == 1
