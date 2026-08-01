# app/db/base.py
"""
Carga explícitamente todos los modelos para que SQLModel.metadata
quede poblada y Alembic autogenerate detecte las tablas.
"""

from sqlmodel import SQLModel

from app.models.ai_conversation import AIConversation  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.business_listing import BusinessListing  # noqa: F401
from app.models.data_source import DataSource, ScrapedDocument, ScrapeJob  # noqa: F401
from app.models.document import Document  # noqa: F401
from app.models.job_listing import JobListing  # noqa: F401
from app.models.migration_process import MigrationProcess  # noqa: F401
from app.models.planner_task import PlannerTask  # noqa: F401
from app.models.school_ranking import SchoolRanking  # noqa: F401
from app.models.service_provider import ServiceProvider  # noqa: F401

# Importa TODOS los modelos aquí (side-effect: registran tablas en metadata)
from app.models.user import User  # noqa: F401
from app.models.user_migration_profile import UserMigrationProfile  # noqa: F401
from app.models.zillow_listing import ZillowListing  # noqa: F401

# Sprint 1 — bounded contexts nuevos (vNext 1.2). core/case_engine es el
# primero: MigrationCase, el aggregate que no existía como código.
from core.case_engine.domain.aggregates import CaseFamilyMember, MigrationCase  # noqa: F401

# Hito 2: Decision Engine (Assessment) + Event Log persistido.
from core.decision_engine.domain.aggregates import Assessment  # noqa: F401

# Hito 3, Sprint 2: Recommendation (baseline docs/RECOMMENDATION_DESIGN.md).
# Hito 4, Sprint 1: Execution Plan (baseline docs/HITO_4_DESIGN.md).
from core.execution_plan.domain.aggregates import ExecutionPlan, PlanStep  # noqa: F401
from core.recommendation.domain.aggregates import Recommendation  # noqa: F401
from core.shared.event_log import PersistedDomainEvent  # noqa: F401

# Resuelve las referencias circulares (forward references) entre los modelos
User.model_rebuild()
MigrationProcess.model_rebuild()
UserMigrationProfile.model_rebuild()
ServiceProvider.model_rebuild()
AIConversation.model_rebuild()
Document.model_rebuild()
DataSource.model_rebuild()
ScrapeJob.model_rebuild()
ScrapedDocument.model_rebuild()
ZillowListing.model_rebuild()
BusinessListing.model_rebuild()
SchoolRanking.model_rebuild()
JobListing.model_rebuild()
PlannerTask.model_rebuild()
AuditLog.model_rebuild()
MigrationCase.model_rebuild()
CaseFamilyMember.model_rebuild()
ExecutionPlan.model_rebuild()
PlanStep.model_rebuild()

metadata = SQLModel.metadata
