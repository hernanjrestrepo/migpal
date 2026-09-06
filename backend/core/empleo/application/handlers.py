"""Empleo — application: handlers (Sprint 10b, Hito 5)."""

from __future__ import annotations

from core.empleo.application.commands import BuscarEmpleosCommand, ConectarEmpleoCommand
from core.empleo.domain.aggregates import EmpleoIntegration
from core.empleo.domain.rules import generate_service_credentials, validate_can_connect
from core.empleo.infrastructure.jobxeeker_client import JobXeekerClient
from core.empleo.infrastructure.repository import EmpleoIntegrationRepository
from core.shared.exceptions import EmpleoNotFound


async def handle_conectar_empleo(
    cmd: ConectarEmpleoCommand, repo: EmpleoIntegrationRepository, client: JobXeekerClient
) -> EmpleoIntegration:
    validate_can_connect(already_connected=repo.get_for_case(cmd.case_id) is not None)

    email, password = generate_service_credentials(cmd.case_id)
    access_token, refresh_token, user_id = await client.register(email=email, password=password, name=cmd.name)

    await client.update_profile(
        access_token=access_token,
        user_id=user_id,
        name=cmd.name,
        email=email,
        target_roles=cmd.target_roles,
        target_industries=cmd.target_industries,
        location_preference=cmd.location_preference,
        experience_level=cmd.experience_level,
        skills=cmd.skills,
    )

    integration = EmpleoIntegration(
        case_id=cmd.case_id, jobxeeker_user_id=user_id, access_token=access_token, refresh_token=refresh_token
    )
    return repo.add(integration)


async def _fresh_token(
    integration: EmpleoIntegration, repo: EmpleoIntegrationRepository, client: JobXeekerClient
) -> str:
    """El access token de JobXeeker dura solo 15 minutos (verificado) --
    más simple y menos propenso a bugs de timezone (ver el que se encontró
    en core/negocio) refrescar siempre antes de usar que llevar la cuenta
    de cuándo vence."""

    access_token, refresh_token = await client.refresh(integration.refresh_token)
    integration.access_token = access_token
    integration.refresh_token = refresh_token
    repo.save(integration)
    return access_token


async def handle_buscar_empleos(
    cmd: BuscarEmpleosCommand, repo: EmpleoIntegrationRepository, client: JobXeekerClient
) -> dict:
    integration = repo.get_for_case(cmd.case_id)
    if integration is None:
        raise EmpleoNotFound(f"El caso {cmd.case_id} todavía no conectó su cuenta de empleo.")

    token = await _fresh_token(integration, repo, client)
    run_result = await client.run_matches(access_token=token, user_id=integration.jobxeeker_user_id)
    matches = await client.list_matches(access_token=token, user_id=integration.jobxeeker_user_id)

    return {"run": run_result, "matches": matches}
