from fastapi import APIRouter
from .config import settings
from app.routes import (
    users,
    auth,
    audit,
    email,
    assessment,
    migration,
    services,
    documents,
    ai_assistant,
    data_sources,
    housing,
    marketplace,
    knowledge,
    planner,
    bot
)

router = APIRouter()

# Include all routers (core MigPAL functionality)
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(users.router)
router.include_router(audit.router)
router.include_router(email.router)

# Core migration assistance routes
router.include_router(assessment.router)
router.include_router(migration.router)
router.include_router(services.router)
router.include_router(documents.router)
router.include_router(ai_assistant.router)
router.include_router(data_sources.router)
router.include_router(housing.router)
router.include_router(marketplace.router)
router.include_router(knowledge.router)
router.include_router(planner.router)
router.include_router(bot.router)


@router.get("/health")
def health():
    return {"status": "ok", "service": settings.service_name}
