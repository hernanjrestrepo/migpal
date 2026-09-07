"""
AdanClient — traducción de fallos de red a AdanIntegrationError.

Sin red real: `httpx.AsyncClient` se reemplaza por un stub. Corrección
encontrada probando el Board Room en vivo (7 sept 2026): un
`httpx.ReadTimeout` no capturado se colaba como 500 genérico hasta el
cliente en vez del 502 documentado (`AdanIntegrationError` es
explícitamente "ADAN respondió con un error, o no respondió") -- ver
docstring de `core/negocio/infrastructure/adan_client.py::AdanClient._post`.
"""

import httpx
import pytest

from core.negocio.infrastructure.adan_client import AdanClient, AdanIntegrationError


class _FakeResponse:
    def __init__(self, status_code, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self.text = text

    def json(self):
        return self._payload


class _FakeAsyncClient:
    def __init__(self, result):
        self._result = result

    def __call__(self, *args, **kwargs):
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def post(self, url, *args, **kwargs):
        if isinstance(self._result, Exception):
            raise self._result
        return self._result


@pytest.mark.asyncio
async def test_read_timeout_becomes_adan_integration_error(monkeypatch):
    """Antes de la corrección, esto dejaba propagar httpx.ReadTimeout sin
    capturar -- FastAPI lo convertía en 500, no en el 502 que
    `adapters/api.py` mapea explícitamente para AdanIntegrationError."""
    import core.negocio.infrastructure.adan_client as adan_client_module

    fake = _FakeAsyncClient(httpx.ReadTimeout("timed out"))
    monkeypatch.setattr(adan_client_module.httpx, "AsyncClient", fake)

    client = AdanClient()
    with pytest.raises(AdanIntegrationError):
        await client.run_board_room(access_token="tok", company_id="c1")


@pytest.mark.asyncio
async def test_connect_error_becomes_adan_integration_error(monkeypatch):
    import core.negocio.infrastructure.adan_client as adan_client_module

    fake = _FakeAsyncClient(httpx.ConnectError("connection refused"))
    monkeypatch.setattr(adan_client_module.httpx, "AsyncClient", fake)

    client = AdanClient()
    with pytest.raises(AdanIntegrationError):
        await client.login(email="a@b.com", password="x")


@pytest.mark.asyncio
async def test_successful_response_still_returns_normally(monkeypatch):
    """La corrección no debe interferir con el camino feliz."""
    import core.negocio.infrastructure.adan_client as adan_client_module

    fake = _FakeAsyncClient(_FakeResponse(200, {"access_token": "abc"}))
    monkeypatch.setattr(adan_client_module.httpx, "AsyncClient", fake)

    client = AdanClient()
    token = await client.login(email="a@b.com", password="x")
    assert token == "abc"


@pytest.mark.asyncio
async def test_non_200_status_still_raises_integration_error(monkeypatch):
    """El camino ya existente (status de error explícito) sigue igual."""
    import core.negocio.infrastructure.adan_client as adan_client_module

    fake = _FakeAsyncClient(_FakeResponse(401, text="unauthorized"))
    monkeypatch.setattr(adan_client_module.httpx, "AsyncClient", fake)

    client = AdanClient()
    with pytest.raises(AdanIntegrationError):
        await client.login(email="a@b.com", password="x")
