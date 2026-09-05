import sys

from pydantic import field_validator
from pydantic_settings import BaseSettings

# Fase 0 (SECURITY-001): valores que nunca deben tener un default utilizable en
# producción. Si el entorno no los define, el arranque falla explícitamente en
# vez de servir con una clave adivinable.
_INSECURE_DEFAULTS = {"change_me", "your_super_secret_jwt_key_change_in_production", ""}


class Settings(BaseSettings):
    service_name: str = "migpal-backend"
    api_prefix: str = "/api/v1"
    environment: str = "development"
    database_url: str = "sqlite:///./migpal.db"

    AUTH_SECRET_KEY: str
    AUTH_ALGORITHM: str = "HS256"
    AUTH_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # AI -- proveedor por defecto: Kimi (Moonshot), API compatible con OpenAI.
    # `ollama` queda como alternativa local (ver app/services/llm_client.py).
    AI_PROVIDER: str = "kimi"
    AI_API_KEY: str = ""
    AI_MODEL: str = "kimi-k2.6"
    KIMI_API_KEY: str = ""
    KIMI_BASE_URL: str = "https://api.moonshot.ai/v1"
    LLM_TIMEOUT_SECONDS: float = 60.0
    LLM_MAX_ATTEMPTS: int = 2
    OLLAMA_URL: str = "http://127.0.0.1:11434"

    # Cache / infra
    REDIS_URL: str = "redis://localhost:6379/0"

    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@migpal.com"
    SMTP_FROM_NAME: str = "MigPAL"

    FRONTEND_URL: str = "http://localhost:3000"
    # Orígenes permitidos por CORS en producción, separados por comas.
    # En desarrollo se agregan localhost:3000/127.0.0.1:3000 automáticamente
    # (ver main.py) -- en producción NO, para no dejar entrar a un localhost
    # atacante contra el API real.
    CORS_ORIGINS: str = ""
    # Rate limit de login/registro. Solo se desactiva en tests (ver
    # tests/conftest.py) -- en producción debe quedar en true.
    RATE_LIMIT_ENABLED: bool = True

    # Telegram Bot - MUST be set in .env (no hardcoded fallback for security)
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_BOT_ENABLED: bool = True

    ENABLE_EXTERNAL_SCRAPERS: bool = False
    GREAT_SCHOOLS_API_KEY: str = ""

    # Logging (backend/app/utils/logging_config.py)
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "console"  # "json" en producción
    LOG_FILE: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"

    @field_validator("AUTH_SECRET_KEY")
    @classmethod
    def _reject_insecure_secret(cls, v: str) -> str:
        if v in _INSECURE_DEFAULTS or len(v) < 16:
            raise ValueError(
                "AUTH_SECRET_KEY debe definirse en el entorno con un valor real "
                "de al menos 16 caracteres — no se permite un default adivinable "
                "(ver docs/SECURITY-001.md)."
            )
        return v


try:
    settings = Settings()
except Exception as exc:  # pragma: no cover - falla intencional y explícita
    sys.stderr.write(f"\n[CONFIG] Variables de entorno inválidas o faltantes: {exc}\n\n")
    raise
