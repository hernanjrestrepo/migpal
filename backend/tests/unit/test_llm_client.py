"""
Cliente LLM agnóstico de proveedor (Kimi por defecto, Ollama alternativo).

Sin red real: `httpx.AsyncClient` se reemplaza por un stub. Cubre las tres
particularidades reales de la API de Kimi que se verificaron contra el
endpoint en vivo antes de escribir el cliente (ver docstring de
`app/services/llm_client.py`): `thinking` solo para modelos que lo admiten,
`temperature` nunca enviada a Kimi, y `content` vacío de un modelo de
razonamiento tratado como fallo (no como respuesta válida).
"""

import pytest

import app.services.llm_client as llm_client
from app.services.llm_client import call_llm


class _FakeResponse:
    def __init__(self, status_code, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self.text = text

    def json(self):
        return self._payload


def _kimi_ok(content: str) -> _FakeResponse:
    return _FakeResponse(200, {"choices": [{"message": {"content": content}, "finish_reason": "stop"}]})


def _kimi_empty_reasoning() -> _FakeResponse:
    """Modelo de razonamiento que gastó el presupuesto pensando: HTTP 200
    pero `content` vacío. Es exactamente lo que devolvió kimi-k2.6 sin
    `thinking.disabled` durante la verificación real."""
    return _FakeResponse(200, {"choices": [{"message": {"content": ""}, "finish_reason": "length"}]})


class _FakeAsyncClient:
    def __init__(self, responses):
        self._responses = list(responses)
        self.call_count = 0
        self.last_json = None
        self.last_headers = None
        self.last_url = None

    def __call__(self, *args, **kwargs):
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def post(self, url, *args, **kwargs):
        self.call_count += 1
        self.last_url = url
        self.last_json = kwargs.get("json")
        self.last_headers = kwargs.get("headers")
        result = self._responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


@pytest.fixture(autouse=True)
def _fast_and_configured(monkeypatch):
    monkeypatch.setattr(llm_client, "LLM_RETRY_BACKOFF_SECONDS", 0)
    monkeypatch.setattr(llm_client, "LLM_MAX_ATTEMPTS", 2)
    monkeypatch.setattr(llm_client, "AI_PROVIDER", "kimi")
    monkeypatch.setattr(llm_client, "AI_MODEL", "kimi-k2.6")
    monkeypatch.setattr(llm_client, "KIMI_API_KEY", "sk-test")
    monkeypatch.setattr(llm_client, "KIMI_BASE_URL", "https://api.example/v1")


@pytest.mark.asyncio
async def test_returns_content_on_first_attempt(monkeypatch):
    fake = _FakeAsyncClient([_kimi_ok("hola")])
    monkeypatch.setattr(llm_client.httpx, "AsyncClient", fake)

    result = await call_llm(system="sys", prompt="p", max_tokens=100)

    assert result == "hola"
    assert fake.call_count == 1
    assert fake.last_url == "https://api.example/v1/chat/completions"
    assert fake.last_headers["Authorization"] == "Bearer sk-test"


@pytest.mark.asyncio
async def test_never_sends_temperature_to_kimi(monkeypatch):
    """La API de Kimi rechaza con HTTP 400 cualquier `temperature` que no
    sea la permitida para el modelo/modo -- por eso no se envía nunca,
    aunque el caller pase una (verificado contra la API real)."""
    fake = _FakeAsyncClient([_kimi_ok("ok")])
    monkeypatch.setattr(llm_client.httpx, "AsyncClient", fake)

    await call_llm(system="sys", prompt="p", max_tokens=100, temperature=0.5)

    assert "temperature" not in fake.last_json


@pytest.mark.asyncio
async def test_disables_thinking_for_models_that_support_it(monkeypatch):
    fake = _FakeAsyncClient([_kimi_ok("ok")])
    monkeypatch.setattr(llm_client.httpx, "AsyncClient", fake)

    await call_llm(system="sys", prompt="p", max_tokens=100)

    assert fake.last_json["thinking"] == {"type": "disabled"}


@pytest.mark.asyncio
async def test_does_not_send_thinking_for_models_that_always_reason(monkeypatch):
    """`kimi-k3` razona siempre y rechaza `thinking` -- enviarlo daría 400."""
    monkeypatch.setattr(llm_client, "AI_MODEL", "kimi-k3")
    fake = _FakeAsyncClient([_kimi_ok("ok")])
    monkeypatch.setattr(llm_client.httpx, "AsyncClient", fake)

    await call_llm(system="sys", prompt="p", max_tokens=100)

    assert "thinking" not in fake.last_json


@pytest.mark.asyncio
async def test_empty_content_from_a_reasoning_model_is_not_a_valid_answer(monkeypatch):
    fake = _FakeAsyncClient([_kimi_empty_reasoning(), _kimi_empty_reasoning()])
    monkeypatch.setattr(llm_client.httpx, "AsyncClient", fake)

    result = await call_llm(system="sys", prompt="p", max_tokens=32)

    assert result is None
    assert fake.call_count == 2


@pytest.mark.asyncio
async def test_retries_once_after_a_network_error_and_then_succeeds(monkeypatch):
    fake = _FakeAsyncClient([TimeoutError("boom"), _kimi_ok("segunda")])
    monkeypatch.setattr(llm_client.httpx, "AsyncClient", fake)

    result = await call_llm(system="sys", prompt="p", max_tokens=100)

    assert result == "segunda"
    assert fake.call_count == 2


@pytest.mark.asyncio
async def test_returns_none_on_http_error_after_retries(monkeypatch):
    fake = _FakeAsyncClient([_FakeResponse(401, text="unauthorized"), _FakeResponse(401, text="unauthorized")])
    monkeypatch.setattr(llm_client.httpx, "AsyncClient", fake)

    assert await call_llm(system="sys", prompt="p", max_tokens=100) is None


@pytest.mark.asyncio
async def test_returns_none_when_api_key_is_missing(monkeypatch):
    monkeypatch.setattr(llm_client, "KIMI_API_KEY", "")
    fake = _FakeAsyncClient([_kimi_ok("no debería llamarse")])
    monkeypatch.setattr(llm_client.httpx, "AsyncClient", fake)

    assert await call_llm(system="sys", prompt="p", max_tokens=100) is None
    assert fake.call_count == 0


@pytest.mark.asyncio
async def test_ollama_provider_delegates_to_the_ollama_client(monkeypatch):
    """`AI_PROVIDER=ollama` debe seguir funcionando sin tocar código."""
    monkeypatch.setattr(llm_client, "AI_PROVIDER", "ollama")
    captured = {}

    async def _fake_call_ollama(*, system, prompt, temperature, num_predict):
        captured.update(system=system, prompt=prompt, temperature=temperature, num_predict=num_predict)
        return "desde ollama"

    monkeypatch.setattr(llm_client, "call_ollama", _fake_call_ollama)

    result = await call_llm(system="sys", prompt="p", max_tokens=123, temperature=0.4)

    assert result == "desde ollama"
    assert captured["temperature"] == 0.4  # a Ollama sí se le pasa
    assert captured["num_predict"] == 123
