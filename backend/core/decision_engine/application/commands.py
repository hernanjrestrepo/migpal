"""Decision Engine — application: comandos."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GenerateAssessmentCommand:
    """`profile_text` ya viene extraído -- Decision Engine no sabe de dónde
    salió (Conversation/AI Adapter, un formulario, o lo que sea mañana).
    Eso es justo lo que lo mantiene desacoplado del LLM."""

    case_id: int
    profile_text: str
