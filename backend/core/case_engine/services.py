"""
Case Engine — comandos (Sprint 1).

Cada función es un comando de transición de estado explícito (Anexo A). Nada
aquí decide -- Decision Engine/Policy Engine/Workflow deciden; este módulo
solo aplica y persiste lo que ya se decidió.
"""

from __future__ import annotations

from datetime import UTC

from sqlmodel import Session, select

from core.case_engine.models import CaseFamilyMember, CaseStatus, MigrationCase
from core.shared.events import event_bus
from core.shared.exceptions import CaseNotFound


def open_case(session: Session, *, user_id: int) -> MigrationCase:
    existing = session.exec(select(MigrationCase).where(MigrationCase.user_id == user_id)).first()
    if existing:
        return existing

    case = MigrationCase(user_id=user_id, status=CaseStatus.DRAFT)
    session.add(case)
    session.commit()
    session.refresh(case)

    event_bus.publish("CaseOpened", {"case_id": case.id, "user_id": user_id})
    return case


def get_case_for_user(session: Session, *, user_id: int) -> MigrationCase:
    case = session.exec(select(MigrationCase).where(MigrationCase.user_id == user_id)).first()
    if not case:
        raise CaseNotFound(f"No hay MigrationCase para user_id={user_id}")
    return case


def update_objective(
    session: Session, *, case: MigrationCase, country: str | None, visa_type: str | None
) -> MigrationCase:
    from datetime import datetime, timezone

    case.objective_country = country
    case.objective_visa_type = visa_type
    case.status = CaseStatus.ACTIVE
    case.updated_at = datetime.now(UTC)
    session.add(case)
    session.commit()
    session.refresh(case)

    event_bus.publish(
        "ProfileUpdated",
        {"case_id": case.id, "objective_country": country, "objective_visa_type": visa_type},
    )
    return case


def add_family_member(
    session: Session, *, case: MigrationCase, full_name: str, relationship_type: str
) -> CaseFamilyMember:
    member = CaseFamilyMember(case_id=case.id, full_name=full_name, relationship_type=relationship_type)
    session.add(member)
    session.commit()
    session.refresh(member)

    event_bus.publish(
        "FamilyMemberAdded",
        {"case_id": case.id, "member_id": member.id, "full_name": full_name},
    )
    return member
