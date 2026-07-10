"""
Case Engine — application: handlers de comando.

Orquestan domain + infrastructure y publican eventos. Esta es la ÚNICA capa
que un adaptador (web_api, telegram) puede llamar -- nunca el repository ni
los aggregates directamente (regla del Sprint 1: "no conectar routers
directamente al dominio").
"""

from __future__ import annotations

from datetime import UTC, datetime

from core.case_engine.application.commands import (
    AddFamilyMemberCommand,
    OpenCaseCommand,
    UpdateObjectiveCommand,
)
from core.case_engine.domain.aggregates import CaseFamilyMember, MigrationCase
from core.case_engine.domain.value_objects import CaseStatus
from core.case_engine.infrastructure.repository import CaseRepository
from core.shared.events import event_bus
from core.shared.exceptions import CaseNotFound


def handle_open_case(cmd: OpenCaseCommand, repo: CaseRepository) -> MigrationCase:
    existing = repo.get_by_user_id(cmd.user_id)
    if existing:
        return existing

    case = MigrationCase(user_id=cmd.user_id, status=CaseStatus.DRAFT)
    case = repo.add(case)

    event_bus.publish("CaseOpened", {"case_id": case.id, "user_id": cmd.user_id})
    return case


def handle_update_objective(cmd: UpdateObjectiveCommand, repo: CaseRepository) -> MigrationCase:
    case = repo.get_by_user_id(cmd.user_id)
    if not case:
        raise CaseNotFound(f"No hay MigrationCase para user_id={cmd.user_id}")

    case.objective_country = cmd.objective_country
    case.objective_visa_type = cmd.objective_visa_type
    case.status = CaseStatus.ACTIVE
    case.updated_at = datetime.now(UTC)
    case = repo.save(case)

    event_bus.publish(
        "ProfileUpdated",
        {
            "case_id": case.id,
            "objective_country": cmd.objective_country,
            "objective_visa_type": cmd.objective_visa_type,
        },
    )
    return case


def handle_add_family_member(cmd: AddFamilyMemberCommand, repo: CaseRepository) -> CaseFamilyMember:
    case = repo.get_by_user_id(cmd.user_id)
    if not case:
        raise CaseNotFound(f"No hay MigrationCase para user_id={cmd.user_id}")

    member = CaseFamilyMember(
        case_id=case.id, full_name=cmd.full_name, relationship_type=cmd.relationship_type
    )
    member = repo.add_family_member(member)

    event_bus.publish(
        "FamilyMemberAdded",
        {"case_id": case.id, "member_id": member.id, "full_name": cmd.full_name},
    )
    return member
