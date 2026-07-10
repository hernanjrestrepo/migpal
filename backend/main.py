from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router as api_router
from app.config import settings
from app.utils.logging_config import get_api_logger, setup_logging

setup_logging(
    level=settings.LOG_LEVEL,
    log_file=settings.LOG_FILE or None,
    json_format=(settings.LOG_FORMAT == "json"),
)
logger = get_api_logger()
logger.info(f"MigPAL backend arrancando — environment={settings.environment}")

app = FastAPI(
    title="MigPAL Backend",
    version="1.0.0",
    description="API REST de MigPAL — ver /health para estado del servicio y "
    "/docs para la documentación interactiva (OpenAPI).",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/")
def root():
    return {
        "name": "MigPAL API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
