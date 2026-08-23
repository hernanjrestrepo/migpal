# This file ensures that all models are imported and registered with SQLModel
# before they are used, which can help prevent circular import issues with relationships.

from .ai_conversation import AIConversation
from .audit_log import AuditLog
from .business_listing import BusinessListing
from .data_source import DataSource, ScrapedDocument, ScrapeJob
from .document import Document
from .job_listing import JobListing
from .migration_process import MigrationProcess
from .planner_task import PlannerTask
from .school_ranking import SchoolRanking
from .service_provider import ServiceProvider
from .user import User
from .user_migration_profile import UserMigrationProfile
from .zillow_listing import ZillowListing

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
