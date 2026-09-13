"""
AI Documents — parseo del veredicto del LLM (post-Hito 5).

Sin red: `call_llm` se reemplaza por un stub. Cubre las particularidades
reales encontradas con ADAN (modelos que no devuelven JSON limpio pese a
la instrucción) aplicadas acá antes de que ocurran en producción: fences
de markdown, verdict inválido, campos faltantes, respuesta vacía."""

import pytest

import app.services.ai_documents as ai_documents
from app.services.ai_documents import FALLBACK_REASONING, NO_TEXT_REASONING, generate_document_verdict


@pytest.mark.asyncio
async def test_empty_extracted_text_never_calls_the_llm(monkeypatch):
    """Si el OCR no extrajo nada, no tiene sentido preguntarle al LLM --
    UNCERTAIN inmediato con una razón distinta a la de fallo del LLM."""
    called = False

    async def _fake_call_llm(**kwargs):
        nonlocal called
        called = True
        return "no debería llegar acá"

    monkeypatch.setattr(ai_documents, "call_llm", _fake_call_llm)

    result = await generate_document_verdict(document_type="Pasaporte", extracted_text="   ")

    assert called is False
    assert result == {"verdict": "UNCERTAIN", "reasoning": NO_TEXT_REASONING, "concerns": []}


@pytest.mark.asyncio
async def test_clean_json_response_is_parsed_correctly(monkeypatch):
    async def _fake_call_llm(**kwargs):
        return '{"verdict": "LIKELY_MATCH", "reasoning": "Menciona un contrato laboral.", "concerns": []}'

    monkeypatch.setattr(ai_documents, "call_llm", _fake_call_llm)

    result = await generate_document_verdict(document_type="Contrato", extracted_text="CONTRATO DE TRABAJO...")

    assert result == {"verdict": "LIKELY_MATCH", "reasoning": "Menciona un contrato laboral.", "concerns": []}


@pytest.mark.asyncio
async def test_response_wrapped_in_markdown_fences_is_still_parsed(monkeypatch):
    """Mismo hallazgo real que con ADAN (adan_client.py): un modelo puede
    envolver el JSON en fences pese a la instrucción explícita de no
    hacerlo."""

    async def _fake_call_llm(**kwargs):
        return '```json\n{"verdict": "LIKELY_MISMATCH", "reasoning": "No coincide.", "concerns": ["falta firma"]}\n```'

    monkeypatch.setattr(ai_documents, "call_llm", _fake_call_llm)

    result = await generate_document_verdict(document_type="Contrato", extracted_text="algo irrelevante")

    assert result["verdict"] == "LIKELY_MISMATCH"
    assert result["concerns"] == ["falta firma"]


@pytest.mark.asyncio
async def test_llm_failure_degrades_to_uncertain_with_visible_reason(monkeypatch):
    """call_llm devuelve None cuando se agotan los reintentos (contrato de
    llm_client.py) -- nunca debe lanzar, nunca debe bloquear el guardado."""

    async def _fake_call_llm(**kwargs):
        return None

    monkeypatch.setattr(ai_documents, "call_llm", _fake_call_llm)

    result = await generate_document_verdict(document_type="Pasaporte", extracted_text="algo de texto")

    assert result == {"verdict": "UNCERTAIN", "reasoning": FALLBACK_REASONING, "concerns": []}


@pytest.mark.asyncio
async def test_unparseable_response_degrades_to_uncertain(monkeypatch):
    async def _fake_call_llm(**kwargs):
        return "esto no es JSON en absoluto, es prosa libre del modelo."

    monkeypatch.setattr(ai_documents, "call_llm", _fake_call_llm)

    result = await generate_document_verdict(document_type="Pasaporte", extracted_text="algo de texto")

    assert result["verdict"] == "UNCERTAIN"
    assert result["reasoning"] == FALLBACK_REASONING


@pytest.mark.asyncio
async def test_invalid_verdict_value_is_normalized_to_uncertain(monkeypatch):
    """El modelo puede inventar un valor de verdict que no está en el
    contrato ("APPROVED", por ejemplo) -- se normaliza, no se propaga tal
    cual (invariante 1 del dominio: solo LIKELY_MATCH/LIKELY_MISMATCH/
    UNCERTAIN existen como veredicto)."""

    async def _fake_call_llm(**kwargs):
        return '{"verdict": "APPROVED", "reasoning": "se ve bien", "concerns": []}'

    monkeypatch.setattr(ai_documents, "call_llm", _fake_call_llm)

    result = await generate_document_verdict(document_type="Pasaporte", extracted_text="algo de texto")

    assert result["verdict"] == "UNCERTAIN"


@pytest.mark.asyncio
async def test_missing_reasoning_field_falls_back_to_default_text(monkeypatch):
    """Invariante 2 -- incluso si el JSON es válido pero le falta
    `reasoning`, nunca queda una razón vacía."""

    async def _fake_call_llm(**kwargs):
        return '{"verdict": "LIKELY_MATCH", "concerns": []}'

    monkeypatch.setattr(ai_documents, "call_llm", _fake_call_llm)

    result = await generate_document_verdict(document_type="Pasaporte", extracted_text="algo de texto")

    assert result["reasoning"] == FALLBACK_REASONING


@pytest.mark.asyncio
async def test_prompt_truncates_very_long_extracted_text(monkeypatch):
    """No tiene sentido (ni es barato) mandar un documento de 50 páginas
    de texto OCR entero al LLM -- se trunca a un tamaño razonable."""
    captured = {}

    async def _fake_call_llm(*, system, prompt, max_tokens):
        captured["prompt_len"] = len(prompt)
        return '{"verdict": "UNCERTAIN", "reasoning": "x", "concerns": []}'

    monkeypatch.setattr(ai_documents, "call_llm", _fake_call_llm)

    await generate_document_verdict(document_type="Pasaporte", extracted_text="A" * 10000)

    assert captured["prompt_len"] < 5000
