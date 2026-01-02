# This file ensures that all models are imported and registered with SQLModel
# before they are used, which can help prevent circular import issues with relationships.

from .user import User
from .audit_log import AuditLog
from .migration_process import MigrationProcess
from .user_migration_profile import UserMigrationProfile
from .service_provider import ServiceProvider
from .ai_conversation import AIConversation
from .document import Document
from .data_source import DataSource, ScrapeJob, ScrapedDocument
from .zillow_listing import ZillowListing
from .business_listing import BusinessListing
from .school_ranking import SchoolRanking
from .job_listing import JobListing
from .planner_task import PlannerTask

# Rebuild models to resolve forward references, the Pydantic v2+ way
User.model_rebuild()
AuditLog.model_rebuild()
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
