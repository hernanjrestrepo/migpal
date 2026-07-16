"""Conversation — application: comandos."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SendMessageCommand:
    case_id: int
    message: str


@dataclass(frozen=True)
class RequestAssessmentCommand:
    case_id: int
    profile_text: str
