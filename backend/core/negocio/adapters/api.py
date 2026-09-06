"""
Negocio — adapters: superficie Web API (Sprint 10, Hito 5).

- 404: caso inexistente, o caso sin cuenta de ADAN conectada todavía.
- 409: el caso ya tiene una cuenta de ADAN conectada (`NegocioInvariantError`).
- 502: ADAN respondió con error o no respondió (`AdanIntegrationError`) --
  es un fallo del sistema externo, no una regla de negocio de MigPAL, por
  eso no es 400/409/404.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

from app.auth import get_current_user
from app.db.session import get_session
from core.case_engine.application.queries import GetCaseForUserQuery, handle_get_case_for_user
from core.case_engine.infrastructure.repository import CaseRepository
from core.identity.domain.aggregates import User
from core.negocio.application.commands import ConectarNegocioCommand, ConsultarJuntaCommand
from core.negocio.application.handlers import handle_conectar_negocio, handle_consultar_junta
from core.negocio.domain.rules import NegocioInvariantError
from core.negocio.infrastructure.adan_client import AdanClient, AdanIntegrationError
from core.negocio.infrastructure.repository import NegocioIntegrationRepository
from core.shared.exceptions import CaseNotFound, NegocioNotFound

router = APIRouter(prefix="/v1/negocio", tags=["negocio"])


def _adan_client() -> AdanClient:
    return AdanClient()


def _get_case_or_404(current_user: User, session: Session):
    case_repo = CaseRepository(session)
    try:
        return handle_get_case_for_user(GetCaseForUserQuery(user_id=current_user.id), case_repo)
    except CaseNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


class ConectarNegocioRequest(BaseModel):
    idea_name: str
    idea_description: str
    industry: str | None = None
    country: str | None = None


class NegocioConectadoRead(BaseModel):
    adan_company_id: str


class ConsultarJuntaRequest(BaseModel):
    message: str


class AgentVoteRead(BaseModel):
    agent: str
    vote: str
    confidence: float
    analysis: str


class JuntaRead(BaseModel):
    decision: str
    score: float
    confidence: float
    summary: str
    votes: list[AgentVoteRead]


@router.post("/connect", response_model=NegocioConectadoRead)
async def conectar_negocio(
    body: ConectarNegocioRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    client: AdanClient = Depends(_adan_client),
):
    case = _get_case_or_404(current_user, session)
    repo = NegocioIntegrationRepository(session)

    try:
        integration = await handle_conectar_negocio(
            ConectarNegocioCommand(
                case_id=case.id, idea_name=body.idea_name, idea_description=body.idea_description,
                industry=body.industry, country=body.country,
            ),
            repo, client,
        )
    except NegocioInvariantError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except AdanIntegrationError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return NegocioConectadoRead(adan_company_id=integration.adan_company_id)


@router.post("/board-room", response_model=JuntaRead)
async def consultar_junta(
    body: ConsultarJuntaRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    client: AdanClient = Depends(_adan_client),
):
    case = _get_case_or_404(current_user, session)
    repo = NegocioIntegrationRepository(session)

    try:
        result = await handle_consultar_junta(
            ConsultarJuntaCommand(case_id=case.id, message=body.message), repo, client
        )
    except NegocioNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except AdanIntegrationError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    votes = [
        AgentVoteRead(
            agent=v.get("agent", "?"),
            vote=v.get("vote", "?"),
            confidence=float(v.get("confidence") or 0),
            analysis=str(v.get("analysis", "")),
        )
        for v in result.get("votes", [])
    ]
    return JuntaRead(
        decision=result.get("decision", "?"),
        score=float(result.get("score") or 0),
        confidence=float(result.get("confidence") or 0),
        summary=result.get("summary", ""),
        votes=votes,
    )
