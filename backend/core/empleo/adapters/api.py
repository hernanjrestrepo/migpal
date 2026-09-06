"""
Empleo — adapters: superficie Web API (Sprint 10b, Hito 5).

- 404: caso inexistente, o caso sin cuenta de JobXeeker conectada todavía.
- 409: el caso ya tiene una cuenta conectada (`EmpleoInvariantError`).
- 502: JobXeeker respondió con error o no respondió (`JobXeekerIntegrationError`).

Nota: `POST /matches` puede devolver 200 con `run.success == false` --
JobXeeker mismo reporta un modo degradado en su matching (ver docstring de
`infrastructure/jobxeeker_client.py`). No se traduce a error HTTP porque
no es un fallo de MigPAL ni de la llamada -- es información real que el
usuario debería poder ver.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.auth import get_current_user
from app.db.session import get_session
from core.case_engine.application.queries import GetCaseForUserQuery, handle_get_case_for_user
from core.case_engine.infrastructure.repository import CaseRepository
from core.empleo.application.commands import BuscarEmpleosCommand, ConectarEmpleoCommand
from core.empleo.application.handlers import handle_buscar_empleos, handle_conectar_empleo
from core.empleo.domain.rules import EmpleoInvariantError
from core.empleo.infrastructure.jobxeeker_client import JobXeekerClient, JobXeekerIntegrationError
from core.empleo.infrastructure.repository import EmpleoIntegrationRepository
from core.identity.domain.aggregates import User
from core.shared.exceptions import CaseNotFound, EmpleoNotFound

router = APIRouter(prefix="/v1/empleo", tags=["empleo"])


def _jobxeeker_client() -> JobXeekerClient:
    return JobXeekerClient()


def _get_case_or_404(current_user: User, session: Session):
    case_repo = CaseRepository(session)
    try:
        return handle_get_case_for_user(GetCaseForUserQuery(user_id=current_user.id), case_repo)
    except CaseNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


class ConectarEmpleoRequest(BaseModel):
    name: str
    target_roles: list[str] = Field(default_factory=list)
    target_industries: list[str] = Field(default_factory=list)
    location_preference: str | None = None
    experience_level: str | None = None
    skills: list[str] = Field(default_factory=list)


class EmpleoConectadoRead(BaseModel):
    jobxeeker_user_id: str


class BuscarEmpleosRead(BaseModel):
    matching_disponible: bool
    mensaje: str | None
    jobs_evaluated: int
    new_matches: int
    matches: list[dict]


@router.post("/connect", response_model=EmpleoConectadoRead)
async def conectar_empleo(
    body: ConectarEmpleoRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    client: JobXeekerClient = Depends(_jobxeeker_client),
):
    case = _get_case_or_404(current_user, session)
    repo = EmpleoIntegrationRepository(session)

    try:
        integration = await handle_conectar_empleo(
            ConectarEmpleoCommand(case_id=case.id, **body.model_dump()), repo, client
        )
    except EmpleoInvariantError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except JobXeekerIntegrationError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return EmpleoConectadoRead(jobxeeker_user_id=integration.jobxeeker_user_id)


@router.post("/matches", response_model=BuscarEmpleosRead)
async def buscar_empleos(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    client: JobXeekerClient = Depends(_jobxeeker_client),
):
    case = _get_case_or_404(current_user, session)
    repo = EmpleoIntegrationRepository(session)

    try:
        result = await handle_buscar_empleos(BuscarEmpleosCommand(case_id=case.id), repo, client)
    except EmpleoNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except JobXeekerIntegrationError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    run = result["run"]
    return BuscarEmpleosRead(
        matching_disponible=bool(run.get("success", False)),
        mensaje=run.get("message"),
        jobs_evaluated=int(run.get("jobs_evaluated") or 0),
        new_matches=int(run.get("new_matches") or 0),
        matches=result["matches"],
    )
