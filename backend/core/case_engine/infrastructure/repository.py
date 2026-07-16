"""
Case Engine — infrastructure: persistencia.

Único lugar del bounded context que conoce `Session`/SQL. La capa
application/ nunca importa `sqlmodel.Session` directamente -- recibe un
CaseRepository ya construido.
"""

from __future__ import annotations

from sqlmodel import Session, select

from core.case_engine.domain.aggregates import CaseFamilyMember, MigrationCase
from core.shared.event_log import persist_event


class CaseRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_user_id(self, user_id: int) -> MigrationCase | None:
        return self._session.exec(select(MigrationCase).where(MigrationCase.user_id == user_id)).first()

    def add(self, case: MigrationCase) -> MigrationCase:
        self._session.add(case)
        self._session.commit()
        self._session.refresh(case)
        # Event Log persistido (Hito 2, regla 5) -- CaseCreated es uno de los
        # tres eventos que este hito exige guardar en base de datos, no solo
        # en el EventBus en memoria.
        persist_event(
            self._session, name="CaseCreated", payload={"case_id": case.id, "user_id": case.user_id}
        )
        return case

    def save(self, case: MigrationCase) -> MigrationCase:
        self._session.add(case)
        self._session.commit()
        self._session.refresh(case)
        return case

    def add_family_member(self, member: CaseFamilyMember) -> CaseFamilyMember:
        self._session.add(member)
        self._session.commit()
        self._session.refresh(member)
        return member
