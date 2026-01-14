from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service_name: str = "migpal-backend"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./migpal.db"

    AUTH_SECRET_KEY: str = "change_me"
    AUTH_ALGORITHM: str = "HS256"
    AUTH_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # AI
    AI_PROVIDER: str = "ollama"
    AI_API_KEY: str = ""
    AI_MODEL: str = "llama3.1:70b"

    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@migpal.com"
    SMTP_FROM_NAME: str = "MigPAL"

    FRONTEND_URL: str = "http://localhost:3000"

    # Telegram Bot - MUST be set in .env (no hardcoded fallback for security)
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_BOT_ENABLED: bool = True

    ENABLE_EXTERNAL_SCRAPERS: bool = False
    GREAT_SCHOOLS_API_KEY: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
