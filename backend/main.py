from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router as api_router
from app.config import settings
from app.utils.logging_config import get_api_logger, setup_logging
from core.case_engine.adapters.api import router as case_router
from core.conversation.adapters.api import router as conversation_router
from core.decision_engine.adapters.api import router as decision_engine_router
from core.execution_plan.adapters.api import router as execution_plan_router
from core.identity.adapters.api import router as identity_router
from core.recommendation.adapters.api import router as recommendation_router

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

# Sprint 1 — Core Vertical (vNext 1.2, A-ADR-003). Superficie de producto
# (Anexo C), no bounded contexts crudos: /v1/case, /v1/auth/register.
app.include_router(case_router)
app.include_router(identity_router)

# Hito 2: un usuario conversa, MigPAL genera un Assessment, queda persistido.
app.include_router(conversation_router)
app.include_router(decision_engine_router)

# Hito 3: Assessment -> Recommendation (ruta, por qué, próximo paso).
app.include_router(recommendation_router)

# Hito 4: Recommendation ACCEPTED -> Execution Plan (pasos a seguir, con
# dependencias y progreso).
app.include_router(execution_plan_router)


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
