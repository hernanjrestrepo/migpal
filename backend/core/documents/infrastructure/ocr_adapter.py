"""
Documents — infrastructure: extracción de texto vía OCR (post-Hito 5).

Determinístico (regla obligatoria 08): el mismo archivo de imagen produce
siempre el mismo texto extraído -- tesseract no tiene aleatoriedad. Esto es
lo que separa esta etapa (pura, testeable con un "caso dorado": misma
imagen, mismo texto) de la etapa de veredicto por IA
(infrastructure/ai_adapter.py, deliberadamente no determinística -- ver
docstring de domain/rules.py).

`pytesseract` llama al binario `tesseract` instalado en el sistema (ver
Dockerfile) -- no es una librería Python pura. `lang="spa+eng"` porque los
documentos migratorios reales de este piloto vienen en español (el
usuario) o en inglés (documentos del país de destino, ej. EE. UU./Canadá/
Australia)."""

from __future__ import annotations

import io

import pytesseract
from PIL import Image, UnidentifiedImageError


class OcrExtractionError(RuntimeError):
    """El archivo no se pudo abrir como imagen, o tesseract falló al
    procesarla -- nunca se confunde con "no había texto legible" (eso es
    un resultado válido: extracted_text vacío, no una excepción)."""


def extract_text(image_bytes: bytes) -> str:
    try:
        image = Image.open(io.BytesIO(image_bytes))
    except UnidentifiedImageError as exc:
        raise OcrExtractionError(f"No se pudo abrir el archivo como imagen: {exc}") from exc

    try:
        return pytesseract.image_to_string(image, lang="spa+eng").strip()
    except pytesseract.TesseractError as exc:
        raise OcrExtractionError(f"Tesseract no pudo procesar la imagen: {exc}") from exc
