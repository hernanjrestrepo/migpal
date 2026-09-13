"""
OCR adapter — contra el binario real de tesseract (post-Hito 5).

A diferencia de tests/unit/, esto NO reemplaza pytesseract por un stub --
genera una imagen real en memoria con PIL y corre el binario `tesseract`
instalado en el contenedor (ver Dockerfile). Si esto falla, es evidencia
de que tesseract-ocr no está instalado o mal configurado, no un problema
de este código.

Reproducibilidad (regla obligatoria 08): la misma imagen produce siempre
el mismo texto -- tesseract no tiene aleatoriedad."""

import io

import pytest
from PIL import Image, ImageDraw

from core.documents.infrastructure.ocr_adapter import OcrExtractionError, extract_text


def _render_text_image(text: str) -> bytes:
    """Genera una imagen simple y de alto contraste -- suficiente para que
    tesseract reconozca texto en mayúsculas grande sin necesitar una
    fuente específica instalada en el contenedor (usa la fuente default
    de Pillow)."""
    image = Image.new("RGB", (600, 150), color="white")
    draw = ImageDraw.Draw(image)
    draw.text((20, 50), text, fill="black")
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def test_extracts_recognizable_text_from_a_real_image():
    image_bytes = _render_text_image("PASAPORTE COLOMBIA")

    result = extract_text(image_bytes)

    # No se exige una coincidencia exacta -- el OCR sobre una fuente
    # generica puede introducir ruido -- pero el contenido reconocible
    # tiene que aparecer.
    assert "PASAPORTE" in result.upper()


def test_same_image_produces_the_same_text_every_time():
    image_bytes = _render_text_image("CONTRATO DE TRABAJO")

    first = extract_text(image_bytes)
    second = extract_text(image_bytes)

    assert first == second


def test_blank_image_produces_empty_or_near_empty_text():
    blank = Image.new("RGB", (200, 100), color="white")
    buf = io.BytesIO()
    blank.save(buf, format="PNG")

    result = extract_text(buf.getvalue())

    assert result.strip() == ""


def test_corrupted_bytes_raise_ocr_extraction_error():
    with pytest.raises(OcrExtractionError):
        extract_text(b"esto no es una imagen en absoluto")
