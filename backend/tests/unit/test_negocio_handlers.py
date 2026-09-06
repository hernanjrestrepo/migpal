"""
Negocio — application handlers (Sprint 10, Hito 5).

`AdanClient` falso -- ninguna llamada de red real. La integración real
contra ADAN se probó a mano (ver docs/HITO_5_DESIGN.md, Sprint 10) y se
verifica de nuevo en tests/contracts/test_negocio_contract.py, marcado
para saltarse si ADAN no está corriendo -- no se hace depender la suite
automática de un tercer servicio siempre encendido.
"""

from datetime import UTC, datetime, timedelta

import pytest

from core.negocio.application.commands import ConectarNegocioCommand, ConsultarJuntaCommand
from core.negocio.application.handlers import handle_conectar_negocio, handle_consultar_junta
from core.negocio.domain.aggregates import NegocioIntegration
from core.negocio.domain.rules import NegocioInvariantError
from core.shared.exceptions import NegocioNotFound


class _FakeAdanClient:
    def __init__(self):
        self.register_calls = []
        self.login_calls = 0
        self.chat_calls = []
        self.board_room_calls = []

    async def register(self, *, email, name, password):
        self.register_calls.append((email, name, password))
        return "fake-access-token", "fake-adan-user-id"

    async def login(self, *, email, password):
        self.login_calls += 1
        return "fake-refreshed-token"

    async def create_company(self, *, access_token, name, description, industry, country):
        return "fake-company-id"

    async def send_chat_message(self, *, access_token, company_id, message):
        self.chat_calls.append((access_token, company_id, message))

    async def run_board_room(self, *, access_token, company_id):
        self.board_room_calls.append((access_token, company_id))
        return {"decision": "PROCEED", "score": 80, "confidence": 75, "summary": "ok", "votes": []}


class _InMemoryNegocioRepository:
    def __init__(self):
        self._by_case = {}
        self._next_id = 1

    def add(self, integration):
        integration.id = self._next_id
        self._next_id += 1
        self._by_case[integration.case_id] = integration
        return integration

    def save(self, integration):
        self._by_case[integration.case_id] = integration
        return integration

    def get_for_case(self, case_id):
        return self._by_case.get(case_id)


@pytest.mark.asyncio
async def test_handle_conectar_negocio_registers_and_creates_company():
    client = _FakeAdanClient()
    repo = _InMemoryNegocioRepository()

    integration = await handle_conectar_negocio(
        ConectarNegocioCommand(case_id=5, idea_name="Lavandería", idea_description="Lavandería en Austin"),
        repo, client,
    )

    assert integration.adan_company_id == "fake-company-id"
    assert integration.adan_email == "migpal-case-5@migpal.internal"
    assert len(client.register_calls) == 1


@pytest.mark.asyncio
async def test_handle_conectar_negocio_raises_if_already_connected():
    client = _FakeAdanClient()
    repo = _InMemoryNegocioRepository()
    await handle_conectar_negocio(
        ConectarNegocioCommand(case_id=5, idea_name="x", idea_description="y"), repo, client
    )

    with pytest.raises(NegocioInvariantError):
        await handle_conectar_negocio(
            ConectarNegocioCommand(case_id=5, idea_name="x", idea_description="y"), repo, client
        )


@pytest.mark.asyncio
async def test_handle_consultar_junta_raises_not_found_without_connection():
    client = _FakeAdanClient()
    repo = _InMemoryNegocioRepository()

    with pytest.raises(NegocioNotFound):
        await handle_consultar_junta(ConsultarJuntaCommand(case_id=5, message="hola"), repo, client)


@pytest.mark.asyncio
async def test_handle_consultar_junta_sends_message_then_runs_board_room():
    client = _FakeAdanClient()
    repo = _InMemoryNegocioRepository()
    await handle_conectar_negocio(
        ConectarNegocioCommand(case_id=5, idea_name="x", idea_description="y"), repo, client
    )

    result = await handle_consultar_junta(ConsultarJuntaCommand(case_id=5, message="¿es viable?"), repo, client)

    assert result["decision"] == "PROCEED"
    assert len(client.chat_calls) == 1
    assert len(client.board_room_calls) == 1
    assert client.login_calls == 0  # el token recién emitido todavía es válido


@pytest.mark.asyncio
async def test_handle_consultar_junta_refreshes_token_when_close_to_expiring():
    client = _FakeAdanClient()
    repo = _InMemoryNegocioRepository()
    integration = await handle_conectar_negocio(
        ConectarNegocioCommand(case_id=5, idea_name="x", idea_description="y"), repo, client
    )
    integration.token_created_at = datetime.now(UTC) - timedelta(hours=23, minutes=30)
    repo.save(integration)

    await handle_consultar_junta(ConsultarJuntaCommand(case_id=5, message="hola"), repo, client)

    assert client.login_calls == 1
    assert repo.get_for_case(5).access_token == "fake-refreshed-token"


def test_negocio_integration_is_a_real_sqlmodel_table():
    # smoke check de que el import y la construcción del modelo no rompen
    integration = NegocioIntegration(
        case_id=1, adan_email="a@b.com", adan_password="x", adan_user_id="u", adan_company_id="c",
        access_token="t",
    )
    assert integration.case_id == 1
