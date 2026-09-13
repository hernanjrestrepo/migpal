"""Documents — application: comandos (post-Hito 5)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SubmitDocumentCommand:
    case_id: int
    document_type: str
    filename: str
    mime_type: str
    content: bytes
