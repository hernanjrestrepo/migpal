"""
JobXeekerClient — traducción de fallos de red a JobXeekerIntegrationError.

Mismo bug y misma corrección que `core/negocio/infrastructure/adan_client.py`
(ver `tests/unit/test_adan_client.py`) -- se aplica acá porque
`jobxeeker_client.py` tenía exactamente el mismo patrón sin capturar
`httpx.HTTPError`.
"""

import httpx
import pytest

from core.empleo.infrastructure.jobxeeker_client import JobXeekerClient, JobXeekerIntegrationError


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

    async def request(self, method, url, *args, **kwargs):
        if isinstance(self._result, Exception):
            raise self._result
        return self._result


@pytest.mark.asyncio
async def test_read_timeout_becomes_jobxeeker_integration_error(monkeypatch):
    import core.empleo.infrastructure.jobxeeker_client as jobxeeker_client_module

    fake = _FakeAsyncClient(httpx.ReadTimeout("timed out"))
    monkeypatch.setattr(jobxeeker_client_module.httpx, "AsyncClient", fake)

    client = JobXeekerClient()
    with pytest.raises(JobXeekerIntegrationError):
        await client.run_matches(access_token="tok", user_id="u1")


@pytest.mark.asyncio
async def test_connect_error_becomes_jobxeeker_integration_error(monkeypatch):
    import core.empleo.infrastructure.jobxeeker_client as jobxeeker_client_module

    fake = _FakeAsyncClient(httpx.ConnectError("connection refused"))
    monkeypatch.setattr(jobxeeker_client_module.httpx, "AsyncClient", fake)

    client = JobXeekerClient()
    with pytest.raises(JobXeekerIntegrationError):
        await client.list_matches(access_token="tok", user_id="u1")


@pytest.mark.asyncio
async def test_successful_response_still_returns_normally(monkeypatch):
    import core.empleo.infrastructure.jobxeeker_client as jobxeeker_client_module

    fake = _FakeAsyncClient(_FakeResponse(200, {"access_token": "a", "refresh_token": "r"}))
    monkeypatch.setattr(jobxeeker_client_module.httpx, "AsyncClient", fake)

    client = JobXeekerClient()
    access, refresh = await client.refresh("old-refresh")
    assert access == "a"
    assert refresh == "r"


@pytest.mark.asyncio
async def test_non_200_status_still_raises_integration_error(monkeypatch):
    import core.empleo.infrastructure.jobxeeker_client as jobxeeker_client_module

    fake = _FakeAsyncClient(_FakeResponse(401, text="unauthorized"))
    monkeypatch.setattr(jobxeeker_client_module.httpx, "AsyncClient", fake)

    client = JobXeekerClient()
    with pytest.raises(JobXeekerIntegrationError):
        await client.refresh("old-refresh")
