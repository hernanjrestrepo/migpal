"""
Documents — infrastructure: guardado del archivo original en disco
(post-Hito 5).

Sin object storage real (S3/GCS/Azure Blob) todavía -- el piloto corre en
un solo host y `/app/data` ya existe en el contenedor (ver Dockerfile).
Reemplazar esto por un adapter de storage real es el primer paso obvio
antes de escalar a más de un host de backend -- deuda documentada, no
escondida, mismo criterio que `NegocioIntegration` guardando la contraseña
de ADAN en texto plano (ver core/negocio/domain/aggregates.py)."""

from __future__ import annotations

import os
import uuid

DOCUMENTS_STORAGE_DIR = os.getenv("DOCUMENTS_STORAGE_DIR", "/app/data/documents")


def save_document_file(*, case_id: int, filename: str, content: bytes) -> str:
    case_dir = os.path.join(DOCUMENTS_STORAGE_DIR, str(case_id))
    os.makedirs(case_dir, exist_ok=True)

    # uuid4 en el nombre: dos subidas del mismo archivo (mismo nombre) no
    # se pisan entre sí.
    safe_name = f"{uuid.uuid4().hex}_{os.path.basename(filename)}"
    path = os.path.join(case_dir, safe_name)
    with open(path, "wb") as f:
        f.write(content)
    return path
