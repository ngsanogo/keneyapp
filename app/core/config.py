"""
Core configuration for KeneyApp.
Manages environment variables and application settings.
"""

from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "KeneyApp"
    APP_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    MFA_ISSUER: str = "KeneyApp"
    MAX_FAILED_LOGIN_ATTEMPTS: int = 5

    # Database
    DATABASE_URL: str = "postgresql://keneyapp:keneyapp@localhost:5432/keneyapp"

    # CORS
    ALLOWED_ORIGINS: Union[str, List[str]] = "http://localhost:3000,http://localhost:8000"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # OAuth2/OIDC
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    MICROSOFT_CLIENT_ID: str = ""
    MICROSOFT_CLIENT_SECRET: str = ""
    OKTA_CLIENT_ID: str = ""
    OKTA_CLIENT_SECRET: str = ""
    OKTA_DOMAIN: str = ""
    APP_URL: str = "http://localhost:8000"

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=True, extra="allow"
    )


_settings = Settings()


if isinstance(_settings.ALLOWED_ORIGINS, str):
    raw_origins = [origin.strip() for origin in _settings.ALLOWED_ORIGINS.split(",")]
    _settings.ALLOWED_ORIGINS = [origin for origin in raw_origins if origin]
elif isinstance(_settings.ALLOWED_ORIGINS, list):
    _settings.ALLOWED_ORIGINS = [origin.strip() for origin in _settings.ALLOWED_ORIGINS]

settings = _settings
