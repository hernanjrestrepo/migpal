from fastapi import FastAPI

from app.config import settings
from app.api import router as api_router

app = FastAPI(title="MigPAL Backend")

app.include_router(api_router, prefix=settings.api_prefix)

