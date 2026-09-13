"""
Documents — application handlers (post-Hito 5).

`extract_text` y el AI adapter se reemplazan por stubs -- ninguna llamada
real a tesseract ni al LLM. El pipeline real (OCR real contra tesseract
instalado en el contenedor) se prueba aparte en
tests/integration/test_ocr_adapter.py."""

import pytest

import core.documents.application.handlers as handlers_module
from core.documents.application.commands import SubmitDocumentCommand
from core.documents.application.handlers import handle_submit_document
from core.documents.domain.value_objects import DocumentReviewStatus, ReviewVerdict
from core.documents.infrastructure.ocr_adapter import OcrExtractionError


class _InMemoryRepo:
    def __init__(self):
        self._by_id = {}
        self._next_id = 1

    def add(self, submission):
        submission.id = self._next_id
        self._next_id += 1
        self._by_id[submission.id] = submission
        return submission

    def get_by_id(self, submission_id):
        return self._by_id.get(submission_id)

    def list_for_case(self, case_id):
        return [s for s in self._by_id.values() if s.case_id == case_id]


class _FakeAiAdapter:
    def __init__(self, result=None):
        self._result = result or {"verdict": "LIKELY_MATCH", "reasoning": "coincide", "concerns": []}
        self.called_with = None

    async def review(self, *, document_type, extracted_text):
        self.called_with = (document_type, extracted_text)
        return self._result


def _cmd(**overrides):
    kwargs = dict(case_id=5, document_type="Pasaporte", filename="foto.jpg", mime_type="image/jpeg", content=b"fake-bytes")
    kwargs.update(overrides)
    return SubmitDocumentCommand(**kwargs)


@pytest.mark.asyncio
async def test_successful_ocr_and_review_produces_reviewed_submission(monkeypatch, tmp_path):
    monkeypatch.setattr(handlers_module, "extract_text", lambda content: "PASAPORTE REPÚBLICA DE COLOMBIA")
    monkeypatch.setattr(handlers_module, "save_document_file", lambda **kw: str(tmp_path / "x.jpg"))

    repo = _InMemoryRepo()
    ai = _FakeAiAdapter({"verdict": "LIKELY_MATCH", "reasoning": "Coincide con un pasaporte.", "concerns": []})

    result = await handle_submit_document(_cmd(), repo, ai)

    assert result.status == DocumentReviewStatus.REVIEWED
    assert result.verdict == ReviewVerdict.LIKELY_MATCH
    assert result.extracted_text == "PASAPORTE REPÚBLICA DE COLOMBIA"
    assert ai.called_with == ("Pasaporte", "PASAPORTE REPÚBLICA DE COLOMBIA")
    assert repo.get_by_id(result.id) is result


@pytest.mark.asyncio
async def test_ocr_extraction_error_produces_ocr_failed_submission_without_calling_ai(monkeypatch, tmp_path):
    def _raise(content):
        raise OcrExtractionError("tesseract no pudo procesar la imagen")

    monkeypatch.setattr(handlers_module, "extract_text", _raise)
    monkeypatch.setattr(handlers_module, "save_document_file", lambda **kw: str(tmp_path / "x.jpg"))

    repo = _InMemoryRepo()
    ai = _FakeAiAdapter()

    result = await handle_submit_document(_cmd(), repo, ai)

    assert result.status == DocumentReviewStatus.OCR_FAILED
    assert result.verdict is None
    assert ai.called_with is None


@pytest.mark.asyncio
async def test_empty_extracted_text_produces_ocr_failed_without_calling_ai(monkeypatch, tmp_path):
    """El OCR "tuvo éxito" (no lanzó) pero no encontró texto -- mismo
    resultado que un fallo de extracción: no tiene sentido pedirle un
    veredicto a la IA sobre texto vacío."""
    monkeypatch.setattr(handlers_module, "extract_text", lambda content: "")
    monkeypatch.setattr(handlers_module, "save_document_file", lambda **kw: str(tmp_path / "x.jpg"))

    repo = _InMemoryRepo()
    ai = _FakeAiAdapter()

    result = await handle_submit_document(_cmd(), repo, ai)

    assert result.status == DocumentReviewStatus.OCR_FAILED
    assert ai.called_with is None


@pytest.mark.asyncio
async def test_file_is_saved_before_ocr_runs(monkeypatch, tmp_path):
    """El archivo original queda guardado incluso si el OCR falla despues
    -- nunca se pierde la subida del usuario."""
    saved_paths = []

    def _save(**kw):
        path = str(tmp_path / "saved.jpg")
        saved_paths.append(path)
        return path

    def _raise(content):
        raise OcrExtractionError("falló")

    monkeypatch.setattr(handlers_module, "save_document_file", _save)
    monkeypatch.setattr(handlers_module, "extract_text", _raise)

    repo = _InMemoryRepo()
    result = await handle_submit_document(_cmd(), repo, _FakeAiAdapter())

    assert len(saved_paths) == 1
    assert result.file_path == saved_paths[0]
