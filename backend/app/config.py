from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service_name: str = "migpal-backend"
    api_prefix: str = "/api/v1"
    gemini_api_key: str

    # JWT Settings
    AUTH_SECRET_KEY: str
    AUTH_ALGORITHM: str = "HS256"
    AUTH_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = "../.env"


settings = Settings()
