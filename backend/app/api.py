from fastapi import APIRouter
from .config import settings
from app.routes import users, referral_levels, auth

router = APIRouter()

# Include other routers
router.include_router(auth.router)
router.include_router(users.router)
router.include_router(referral_levels.router)


@router.get("/health")
def health():
    return {"status": "ok", "service": settings.service_name}
