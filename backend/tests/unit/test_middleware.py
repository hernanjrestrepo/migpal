"""
Middleware transversal: rate limit, cabeceras de seguridad y request-id.

El rate limit está desactivado en el resto de la suite
(`RATE_LIMIT_ENABLED=false` en conftest.py) porque los contract tests
comparten una única IP y chocarían con el cupo. Acá se prueba el limitador
de forma directa, con su propia app mínima, para que el comportamiento siga
cubierto en vez de quedar sin verificar.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.middleware as mw
from app.middleware import RateLimitMiddleware, RequestIdMiddleware, SecurityHeadersMiddleware


def _app_with(middleware_cls) -> FastAPI:
    application = FastAPI()
    application.add_middleware(middleware_cls)

    @application.post("/api/v1/auth/token")
    def token():
        return {"ok": True}

    @application.post("/v1/auth/register")
    def register():
        return {"ok": True}

    @application.get("/libre")
    def libre():
        return {"ok": True}

    return application


@pytest.fixture(autouse=True)
def _clean_state(monkeypatch):
    """El contador es un dict a nivel de módulo: sin limpiarlo, un test
    arrastraría los golpes del anterior."""
    mw._hits.clear()
    monkeypatch.setattr(mw, "RATE_LIMIT_ENABLED", True)
    yield
    mw._hits.clear()


# ------------------------------------------------------------ rate limit


def test_permite_hasta_el_cupo_y_luego_devuelve_429():
    client = TestClient(_app_with(RateLimitMiddleware))
    # El cupo de /api/v1/auth/token es 10 por minuto.
    for _ in range(10):
        assert client.post("/api/v1/auth/token").status_code == 200

    blocked = client.post("/api/v1/auth/token")
    assert blocked.status_code == 429
    assert "Retry-After" in blocked.headers
    assert "Demasiados intentos" in blocked.json()["detail"]


def test_el_registro_tiene_su_propio_cupo_mas_estricto():
    client = TestClient(_app_with(RateLimitMiddleware))
    for _ in range(5):
        assert client.post("/v1/auth/register").status_code == 200
    assert client.post("/v1/auth/register").status_code == 429


def test_cada_ruta_lleva_su_contador_por_separado():
    """Agotar el cupo del registro no debe bloquear el login."""
    client = TestClient(_app_with(RateLimitMiddleware))
    for _ in range(5):
        client.post("/v1/auth/register")
    assert client.post("/v1/auth/register").status_code == 429
    assert client.post("/api/v1/auth/token").status_code == 200


def test_no_limita_rutas_fuera_de_la_lista():
    client = TestClient(_app_with(RateLimitMiddleware))
    for _ in range(30):
        assert client.get("/libre").status_code == 200


def test_ips_distintas_no_comparten_cupo():
    """El límite es por IP: un atacante no debe poder bloquear a terceros."""
    client = TestClient(_app_with(RateLimitMiddleware))
    for _ in range(10):
        client.post("/api/v1/auth/token", headers={"X-Forwarded-For": "10.0.0.1"})
    assert client.post("/api/v1/auth/token", headers={"X-Forwarded-For": "10.0.0.1"}).status_code == 429
    assert client.post("/api/v1/auth/token", headers={"X-Forwarded-For": "10.0.0.2"}).status_code == 200


def test_toma_la_primera_ip_de_x_forwarded_for():
    """Detrás de varios proxies la cabecera trae una cadena; la del cliente
    original es la primera."""
    client = TestClient(_app_with(RateLimitMiddleware))
    chain = {"X-Forwarded-For": "10.0.0.9, 172.16.0.1, 192.168.1.1"}
    for _ in range(10):
        client.post("/api/v1/auth/token", headers=chain)
    assert client.post("/api/v1/auth/token", headers={"X-Forwarded-For": "10.0.0.9"}).status_code == 429


def test_se_puede_desactivar_por_configuracion(monkeypatch):
    monkeypatch.setattr(mw, "RATE_LIMIT_ENABLED", False)
    client = TestClient(_app_with(RateLimitMiddleware))
    for _ in range(30):
        assert client.post("/api/v1/auth/token").status_code == 200


# ------------------------------------------------- cabeceras de seguridad


def test_agrega_las_cabeceras_de_seguridad():
    client = TestClient(_app_with(SecurityHeadersMiddleware))
    headers = client.get("/libre").headers
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    assert headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "geolocation=()" in headers["Permissions-Policy"]


# --------------------------------------------------------- request id


def test_genera_un_request_id_si_no_viene():
    client = TestClient(_app_with(RequestIdMiddleware))
    assert client.get("/libre").headers["X-Request-ID"]


def test_respeta_el_request_id_del_proxy():
    """Generar uno nuevo rompería la traza que ya venía del borde."""
    client = TestClient(_app_with(RequestIdMiddleware))
    res = client.get("/libre", headers={"X-Request-ID": "traza-existente"})
    assert res.headers["X-Request-ID"] == "traza-existente"
