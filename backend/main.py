import redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlmodel import Session, select

from app.api import router as api_router
from app.config import settings
from app.db.session import engine
from app.middleware import RateLimitMiddleware, RequestIdMiddleware, SecurityHeadersMiddleware
from app.utils.logging_config import get_api_logger, setup_logging
from core.budget.adapters.api import router as budget_router
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

# Middleware. Orden: el último agregado es el más externo, así que
# RequestId envuelve a todo y su id ya está disponible para el resto.
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)

# CORS: en producción se define con CORS_ORIGINS (lista separada por comas).
# Los orígenes de desarrollo solo se agregan fuera de producción -- dejarlos
# siempre permitiría que un localhost atacante hablara con el API real.
_cors_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
if settings.environment != "production":
    _cors_origins += ["http://localhost:3000", "http://127.0.0.1:3000"]
if settings.FRONTEND_URL and settings.FRONTEND_URL not in _cors_origins:
    _cors_origins.append(settings.FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)
app.add_middleware(RequestIdMiddleware)

logger.info(f"CORS habilitado para: {_cors_origins}")

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

# Hito 5, Sprint 1: presupuesto total de migrar y punto de equilibrio
# (docs/HITO_5_DESIGN.md §2).
app.include_router(budget_router)


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
    """Liveness: ¿está vivo el proceso? Lo usa el healthcheck de Docker.
    Deliberadamente no toca la base de datos -- si Postgres se cae, no
    queremos que el orquestador reinicie un backend que está perfectamente
    sano."""
    return {"status": "healthy"}


@app.get("/ready")
def readiness_check():
    """Readiness: ¿puede este proceso atender tráfico real? Verifica las
    dependencias de las que depende cada request. Un balanceador debe sacar
    de rotación una instancia que responda 503 acá."""
    checks: dict[str, str] = {}
    ready = True

    try:
        with Session(engine) as session:
            session.exec(select(1))
        checks["database"] = "ok"
    except Exception as exc:  # noqa: BLE001 -- el detalle se reporta, no se propaga
        checks["database"] = f"error: {type(exc).__name__}"
        ready = False

    try:
        redis.from_url(settings.REDIS_URL, socket_connect_timeout=2).ping()
        checks["redis"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["redis"] = f"error: {type(exc).__name__}"
        ready = False

    # El proveedor de IA no entra en readiness: si el LLM falla, el producto
    # se degrada (narrative_summary cae a su fallback) pero sigue sirviendo.
    checks["llm_provider"] = settings.AI_PROVIDER

    return JSONResponse(
        status_code=200 if ready else 503,
        content={"status": "ready" if ready else "degraded", "checks": checks},
    )
