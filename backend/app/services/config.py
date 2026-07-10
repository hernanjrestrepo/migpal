"""
MigPAL Configuration Module
Configuración centralizada para el bot

All configuration should be loaded from environment variables
with sensible defaults for development.
"""

import os
from pathlib import Path

# Load .env file if exists
try:
    from dotenv import load_dotenv

    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass


class Config:
    """Central configuration class"""

    # ============== BOT CONFIG ==============
    BOT_NAME = "MigPAL"
    BOT_USERNAME = "@MigPAL_Bot"
    BOT_URL = "https://t.me/MigPAL_Bot"

    # Telegram - MUST be set in .env (no hardcoded fallback for security)
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

    # ============== AI CONFIG ==============
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "ollama")
    AI_MODEL: str = os.getenv("AI_MODEL", "qwen2.5:7b")
    OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")

    # OpenAI (if using)
    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # ============== PATHS ==============
    BASE_DIR = Path(__file__).parent.parent.parent
    DATA_DIR = BASE_DIR / "data"
    CASES_DIR = DATA_DIR / "cases"
    REPORTS_DIR = DATA_DIR / "reports"
    BACKUPS_DIR = BASE_DIR / "backups"
    LOGS_DIR = BASE_DIR / "logs"

    # ============== SECURITY ==============
    ENCRYPTION_KEY: str = os.getenv("MIGPAL_ENCRYPTION_KEY", "migpal_default_key_change_in_production_2026")

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))
    RATE_LIMIT_PER_HOUR: int = int(os.getenv("RATE_LIMIT_PER_HOUR", "200"))
    RATE_LIMIT_BLOCK_MINUTES: int = int(os.getenv("RATE_LIMIT_BLOCK_MINUTES", "5"))

    # ============== DATABASE ==============
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR}/migpal.db")

    # ============== FEATURES ==============
    ENABLE_OCR: bool = os.getenv("ENABLE_OCR", "true").lower() == "true"
    ENABLE_PDF_REPORTS: bool = os.getenv("ENABLE_PDF_REPORTS", "true").lower() == "true"
    ENABLE_NOTIFICATIONS: bool = os.getenv("ENABLE_NOTIFICATIONS", "true").lower() == "true"
    ENABLE_ANALYTICS: bool = os.getenv("ENABLE_ANALYTICS", "false").lower() == "true"

    # ============== BACKUP ==============
    BACKUP_ENABLED: bool = os.getenv("BACKUP_ENABLED", "true").lower() == "true"
    BACKUP_INTERVAL_HOURS: int = int(os.getenv("BACKUP_INTERVAL_HOURS", "6"))
    BACKUP_MAX_COUNT: int = int(os.getenv("BACKUP_MAX_COUNT", "30"))

    # ============== LOGGING ==============
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # ============== EXTERNAL SERVICES ==============
    # For future integrations
    USCIS_API_KEY: str | None = os.getenv("USCIS_API_KEY")
    IRCC_API_KEY: str | None = os.getenv("IRCC_API_KEY")

    @classmethod
    def ensure_directories(cls):
        """Create necessary directories if they don't exist"""
        for dir_path in [cls.DATA_DIR, cls.CASES_DIR, cls.REPORTS_DIR, cls.BACKUPS_DIR, cls.LOGS_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_env_summary(cls) -> dict:
        """Get a summary of current configuration (safe for logging)"""
        return {
            "bot_name": cls.BOT_NAME,
            "ai_provider": cls.AI_PROVIDER,
            "ai_model": cls.AI_MODEL,
            "features": {
                "ocr": cls.ENABLE_OCR,
                "pdf_reports": cls.ENABLE_PDF_REPORTS,
                "notifications": cls.ENABLE_NOTIFICATIONS,
                "analytics": cls.ENABLE_ANALYTICS,
            },
            "security": {
                "rate_limit_per_minute": cls.RATE_LIMIT_PER_MINUTE,
                "rate_limit_per_hour": cls.RATE_LIMIT_PER_HOUR,
            },
            "backup": {
                "enabled": cls.BACKUP_ENABLED,
                "interval_hours": cls.BACKUP_INTERVAL_HOURS,
            },
        }

    @classmethod
    def validate(cls) -> list:
        """Validate configuration and return list of warnings"""
        warnings = []

        if cls.ENCRYPTION_KEY == "migpal_default_key_change_in_production_2026":
            warnings.append("⚠️ Using default encryption key - change in production!")

        if not cls.TELEGRAM_BOT_TOKEN:
            warnings.append("❌ TELEGRAM_BOT_TOKEN not set!")

        if cls.AI_PROVIDER == "openai" and not cls.OPENAI_API_KEY:
            warnings.append("⚠️ OpenAI selected but OPENAI_API_KEY not set")

        return warnings


# Create singleton instance
config = Config()

# Ensure directories exist
config.ensure_directories()

# Export
__all__ = ["config", "Config"]
