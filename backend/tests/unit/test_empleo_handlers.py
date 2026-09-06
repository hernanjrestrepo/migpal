"""
Empleo — application handlers (Sprint 10b, Hito 5).

`JobXeekerClient` falso -- ninguna llamada de red real. La integración
real contra JobXeeker se probó a mano y se verifica de nuevo en
tests/contracts/test_empleo_contract.py, marcado para saltarse si
JobXeeker no está corriendo.
"""

import pytest

from core.empleo.application.commands import BuscarEmpleosCommand, ConectarEmpleoCommand
from core.empleo.application.handlers import handle_buscar_empleos, handle_conectar_empleo
from core.empleo.domain.rules import EmpleoInvariantError
from core.shared.exceptions import EmpleoNotFound


class _FakeJobXeekerClient:
    def __init__(self, match_success: bool = True):
        self.match_success = match_success
        self.register_calls = []
        self.refresh_calls = 0
        self.profile_calls = []

    async def register(self, *, email, password, name):
        self.register_calls.append((email, name))
        return "fake-access", "fake-refresh-1", "usr_fake"

    async def refresh(self, refresh_token):
        self.refresh_calls += 1
        return "fake-access-2", f"fake-refresh-{self.refresh_calls + 1}"

    async def update_profile(self, **kwargs):
        self.profile_calls.append(kwargs)

    async def run_matches(self, *, access_token, user_id):
        if self.match_success:
            return {"success": True, "jobs_evaluated": 12, "new_matches": 3, "top_match": 0.94}
        return {
            "success": False, "analysis_status": "degraded_mode",
            "message": "'<' not supported between instances of 'NoneType' and 'float'",
            "jobs_evaluated": 0, "new_matches": 0, "top_match": 0,
        }

    async def list_matches(self, *, access_token, user_id):
        return [{"job_title": "Senior Backend Engineer", "score": 0.94}] if self.match_success else []


class _InMemoryEmpleoRepository:
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
async def test_handle_conectar_empleo_registers_and_updates_profile():
    client = _FakeJobXeekerClient()
    repo = _InMemoryEmpleoRepository()

    integration = await handle_conectar_empleo(
        ConectarEmpleoCommand(case_id=5, name="Camilo Restrepo", skills=["Python"]), repo, client
    )

    assert integration.jobxeeker_user_id == "usr_fake"
    assert len(client.profile_calls) == 1


@pytest.mark.asyncio
async def test_handle_conectar_empleo_raises_if_already_connected():
    client = _FakeJobXeekerClient()
    repo = _InMemoryEmpleoRepository()
    await handle_conectar_empleo(ConectarEmpleoCommand(case_id=5, name="x"), repo, client)

    with pytest.raises(EmpleoInvariantError):
        await handle_conectar_empleo(ConectarEmpleoCommand(case_id=5, name="x"), repo, client)


@pytest.mark.asyncio
async def test_handle_buscar_empleos_raises_not_found_without_connection():
    client = _FakeJobXeekerClient()
    repo = _InMemoryEmpleoRepository()

    with pytest.raises(EmpleoNotFound):
        await handle_buscar_empleos(BuscarEmpleosCommand(case_id=5), repo, client)


@pytest.mark.asyncio
async def test_handle_buscar_empleos_refreshes_token_every_call():
    client = _FakeJobXeekerClient()
    repo = _InMemoryEmpleoRepository()
    await handle_conectar_empleo(ConectarEmpleoCommand(case_id=5, name="x"), repo, client)

    result = await handle_buscar_empleos(BuscarEmpleosCommand(case_id=5), repo, client)

    assert client.refresh_calls == 1
    assert result["run"]["success"] is True
    assert len(result["matches"]) == 1
    assert repo.get_for_case(5).access_token == "fake-access-2"


@pytest.mark.asyncio
async def test_handle_buscar_empleos_surfaces_degraded_mode_without_raising():
    client = _FakeJobXeekerClient(match_success=False)
    repo = _InMemoryEmpleoRepository()
    await handle_conectar_empleo(ConectarEmpleoCommand(case_id=5, name="x"), repo, client)

    result = await handle_buscar_empleos(BuscarEmpleosCommand(case_id=5), repo, client)

    assert result["run"]["success"] is False
    assert "NoneType" in result["run"]["message"]
