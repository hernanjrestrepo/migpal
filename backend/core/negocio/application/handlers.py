"""Negocio — application: handlers (Sprint 10, Hito 5)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from core.negocio.application.commands import ConectarNegocioCommand, ConsultarJuntaCommand
from core.negocio.domain.aggregates import NegocioIntegration
from core.negocio.domain.rules import generate_service_credentials, validate_can_connect
from core.negocio.infrastructure.adan_client import AdanClient
from core.negocio.infrastructure.repository import NegocioIntegrationRepository
from core.shared.exceptions import NegocioNotFound

# ADAN no expone refresh token (ver docstring de adan_client.py); su JWT
# dura 24h. Se renueva con margen -- nunca justo al filo del vencimiento.
TOKEN_REFRESH_MARGIN = timedelta(hours=1)
TOKEN_LIFETIME = timedelta(hours=24)


async def handle_conectar_negocio(
    cmd: ConectarNegocioCommand, repo: NegocioIntegrationRepository, client: AdanClient
) -> NegocioIntegration:
    validate_can_connect(already_connected=repo.get_for_case(cmd.case_id) is not None)

    email, password = generate_service_credentials(cmd.case_id)
    access_token, adan_user_id = await client.register(
        email=email, name=f"MigPAL Caso {cmd.case_id}", password=password
    )
    company_id = await client.create_company(
        access_token=access_token,
        name=cmd.idea_name,
        description=cmd.idea_description,
        industry=cmd.industry,
        country=cmd.country,
    )

    integration = NegocioIntegration(
        case_id=cmd.case_id,
        adan_email=email,
        adan_password=password,
        adan_user_id=adan_user_id,
        adan_company_id=company_id,
        access_token=access_token,
    )
    return repo.add(integration)


async def _ensure_fresh_token(
    integration: NegocioIntegration, repo: NegocioIntegrationRepository, client: AdanClient
) -> str:
    # Postgres devuelve el datetime sin tzinfo al releerlo aunque se haya
    # guardado en UTC (columna `DateTime` sin `timezone=True`) -- se
    # normaliza acá en vez de cambiar el tipo de columna en todo el repo.
    token_created_at = integration.token_created_at
    if token_created_at.tzinfo is None:
        token_created_at = token_created_at.replace(tzinfo=UTC)

    token_age = datetime.now(UTC) - token_created_at
    if token_age < TOKEN_LIFETIME - TOKEN_REFRESH_MARGIN:
        return integration.access_token

    integration.access_token = await client.login(email=integration.adan_email, password=integration.adan_password)
    integration.token_created_at = datetime.now(UTC)
    repo.save(integration)
    return integration.access_token


async def handle_consultar_junta(
    cmd: ConsultarJuntaCommand, repo: NegocioIntegrationRepository, client: AdanClient
) -> dict:
    integration = repo.get_for_case(cmd.case_id)
    if integration is None:
        raise NegocioNotFound(f"El caso {cmd.case_id} todavía no conectó su cuenta de negocio.")

    token = await _ensure_fresh_token(integration, repo, client)
    await client.send_chat_message(access_token=token, company_id=integration.adan_company_id, message=cmd.message)
    return await client.run_board_room(access_token=token, company_id=integration.adan_company_id)
