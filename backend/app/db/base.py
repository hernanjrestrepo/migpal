# app/db/base.py
"""
Carga explícitamente todos los modelos para que SQLModel.metadata
quede poblada y Alembic autogenerate detecte las tablas.
"""

from sqlmodel import SQLModel

# Importa TODOS los modelos aquí (side-effect: registran tablas en metadata)
from app.models.user import User  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.migration_process import MigrationProcess  # noqa: F401
from app.models.user_migration_profile import UserMigrationProfile  # noqa: F401
from app.models.service_provider import ServiceProvider  # noqa: F401
from app.models.ai_conversation import AIConversation  # noqa: F401
from app.models.document import Document  # noqa: F401
from app.models.data_source import DataSource, ScrapeJob, ScrapedDocument  # noqa: F401
from app.models.zillow_listing import ZillowListing  # noqa: F401
from app.models.business_listing import BusinessListing  # noqa: F401
from app.models.school_ranking import SchoolRanking  # noqa: F401
from app.models.job_listing import JobListing  # noqa: F401
from app.models.planner_task import PlannerTask  # noqa: F401

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

metadata = SQLModel.metadata
