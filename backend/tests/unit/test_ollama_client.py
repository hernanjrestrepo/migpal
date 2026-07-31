"""
Cliente Ollama compartido -- timeout configurable + reintento (estabilización, Hito 3).

Sin red real: `httpx.AsyncClient` se reemplaza por un stub. Prueba el
comportamiento de reintento que corrige el timeout observado en
tests/integration/test_recommendation_narrative_real_llm.py durante el
cierre de Hito 3 -- no la latencia real de Ollama (eso sigue viviendo en
los tests de integración, contra Ollama real).
"""

import pytest

import app.services.ollama_client as ollama_client
from app.services.ollama_client import call_ollama


class _FakeResponse:
    def __init__(self, status_code, text=""):
        self.status_code = status_code
        self._text = text

    def json(self):
        return {"response": self._text}


class _FakeAsyncClient:
    """Reemplaza `httpx.AsyncClient` -- `responses` es una cola de
    valores/excepciones a devolver, una por intento."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.call_count = 0

    def __call__(self, *args, **kwargs):
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def post(self, *args, **kwargs):
        self.call_count += 1
        result = self._responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


@pytest.fixture(autouse=True)
def _no_real_sleep(monkeypatch):
    """El backoff entre reintentos no debe ralentizar la suite."""
    monkeypatch.setattr(ollama_client, "OLLAMA_RETRY_BACKOFF_SECONDS", 0)
    monkeypatch.setattr(ollama_client, "OLLAMA_MAX_ATTEMPTS", 2)


@pytest.mark.asyncio
async def test_succeeds_on_first_attempt_without_retrying(monkeypatch):
    fake = _FakeAsyncClient([_FakeResponse(200, "hola")])
    monkeypatch.setattr(ollama_client.httpx, "AsyncClient", fake)

    result = await call_ollama(system="sys", prompt="p", temperature=0.5, num_predict=100)

    assert result == "hola"
    assert fake.call_count == 1


@pytest.mark.asyncio
async def test_retries_once_after_a_timeout_and_then_succeeds(monkeypatch):
    """Este es exactamente el escenario que falló en la sesión de cierre:
    el primer intento agota el timeout, el segundo responde bien."""
    fake = _FakeAsyncClient([TimeoutError("simulated timeout"), _FakeResponse(200, "respuesta real")])
    monkeypatch.setattr(ollama_client.httpx, "AsyncClient", fake)

    result = await call_ollama(system="sys", prompt="p", temperature=0.5, num_predict=100)

    assert result == "respuesta real"
    assert fake.call_count == 2


@pytest.mark.asyncio
async def test_returns_none_after_exhausting_all_retries(monkeypatch):
    fake = _FakeAsyncClient([TimeoutError("t1"), TimeoutError("t2")])
    monkeypatch.setattr(ollama_client.httpx, "AsyncClient", fake)

    result = await call_ollama(system="sys", prompt="p", temperature=0.5, num_predict=100)

    assert result is None
    assert fake.call_count == 2


@pytest.mark.asyncio
async def test_returns_none_on_non_200_after_retries(monkeypatch):
    fake = _FakeAsyncClient([_FakeResponse(500), _FakeResponse(500)])
    monkeypatch.setattr(ollama_client.httpx, "AsyncClient", fake)

    result = await call_ollama(system="sys", prompt="p", temperature=0.5, num_predict=100)
    assert result is None


@pytest.mark.asyncio
async def test_returns_none_on_empty_text_response(monkeypatch):
    fake = _FakeAsyncClient([_FakeResponse(200, ""), _FakeResponse(200, "")])
    monkeypatch.setattr(ollama_client.httpx, "AsyncClient", fake)

    result = await call_ollama(system="sys", prompt="p", temperature=0.5, num_predict=100)
    assert result is None


def test_timeout_and_attempts_are_configurable_via_env(monkeypatch):
    monkeypatch.setenv("OLLAMA_TIMEOUT_SECONDS", "45")
    monkeypatch.setenv("OLLAMA_MAX_ATTEMPTS", "3")

    import importlib

    reloaded = importlib.reload(ollama_client)
    try:
        assert reloaded.OLLAMA_TIMEOUT_SECONDS == 45.0
        assert reloaded.OLLAMA_MAX_ATTEMPTS == 3
    finally:
        monkeypatch.delenv("OLLAMA_TIMEOUT_SECONDS", raising=False)
        monkeypatch.delenv("OLLAMA_MAX_ATTEMPTS", raising=False)
        importlib.reload(ollama_client)
