"""
Core configuration for KeneyApp.
Manages environment variables and application settings.

Includes a small guard that removes empty-string environment overrides for
typed settings (bool/int) to avoid ValidationError when a blank value is
present in the shell or .env. This lets defaults apply as intended.
"""

import os
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


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

    # Bootstrap / default credentials (for tests & local environments)
    ENABLE_BOOTSTRAP_ADMIN: bool = True
    BOOTSTRAP_TENANT_NAME: str = "Default Tenant"
    BOOTSTRAP_TENANT_SLUG: str = "default"
    BOOTSTRAP_ADMIN_USERNAME: str = "admin"
    BOOTSTRAP_ADMIN_PASSWORD: str = "admin123"
    BOOTSTRAP_ADMIN_EMAIL: str = "admin@keneyapp.local"
    BOOTSTRAP_ADMIN_FULL_NAME: str = "System Administrator"

    # CORS
    ALLOWED_ORIGINS: Union[str, List[str]] = (
        "http://localhost:3000,http://localhost:8000"
    )

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

    # ------------------------------------------------------------------
    # Validators to coerce empty-string envs to sensible defaults
    # ------------------------------------------------------------------
    @field_validator("DEBUG", mode="before")
    @classmethod
    def _coerce_debug(cls, v):
        if v in ("", None):
            return False
        return v

    @field_validator("ACCESS_TOKEN_EXPIRE_MINUTES", mode="before")
    @classmethod
    def _coerce_token_exp(cls, v):
        if v in ("", None):
            return 30
        return v

    @field_validator("MAX_FAILED_LOGIN_ATTEMPTS", mode="before")
    @classmethod
    def _coerce_max_attempts(cls, v):
        if v in ("", None):
            return 5
        return v

    @field_validator("ENABLE_BOOTSTRAP_ADMIN", mode="before")
    @classmethod
    def _coerce_bootstrap_admin(cls, v):
        if v in ("", None):
            return True
        return v

    @field_validator("REDIS_PORT", mode="before")
    @classmethod
    def _coerce_redis_port(cls, v):
        if v in ("", None):
            return 6379
        return v

    @field_validator("REDIS_DB", mode="before")
    @classmethod
    def _coerce_redis_db(cls, v):
        if v in ("", None):
            return 0
        return v

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def _coerce_database_url(cls, v):
        if v in ("", None):
            return "postgresql://keneyapp:keneyapp@localhost:5432/keneyapp"
        return v

    @field_validator("APP_NAME", mode="before")
    @classmethod
    def _coerce_app_name(cls, v):
        if v in ("", None):
            return "KeneyApp"
        return v
    
    @field_validator("APP_VERSION", mode="before")
    @classmethod
    def _coerce_app_version(cls, v):
        if v in ("", None):
            return "1.0.0"
        return v
    
    @field_validator("API_V1_PREFIX", mode="before")
    @classmethod
    def _coerce_api_prefix(cls, v):
        if v in ("", None):
            return "/api/v1"
        return v

    @field_validator("ALGORITHM", mode="before")
    @classmethod
    def _coerce_algorithm(cls, v):
        # Ensure a supported JWT algorithm is set
        if v in ("", None):
            return "HS256"
        return v

    # Bootstrap defaults coercion (avoid blanks disabling bootstrap implicitly)
    @field_validator("BOOTSTRAP_ADMIN_USERNAME", mode="before")
    @classmethod
    def _coerce_bootstrap_username(cls, v):
        if v in ("", None):
            return "admin"
        return v

    @field_validator("BOOTSTRAP_ADMIN_PASSWORD", mode="before")
    @classmethod
    def _coerce_bootstrap_password(cls, v):
        if v in ("", None):
            return "admin123"
        return v

    @field_validator("BOOTSTRAP_TENANT_SLUG", mode="before")
    @classmethod
    def _coerce_bootstrap_slug(cls, v):
        if v in ("", None):
            return "default"
        return v

    @field_validator("BOOTSTRAP_TENANT_NAME", mode="before")
    @classmethod
    def _coerce_bootstrap_tenant_name(cls, v):
        if v in ("", None):
            return "Default Tenant"
        return v

    @field_validator("BOOTSTRAP_ADMIN_EMAIL", mode="before")
    @classmethod
    def _coerce_bootstrap_email(cls, v):
        if v in ("", None):
            return "admin@keneyapp.local"
        return v

    @field_validator("BOOTSTRAP_ADMIN_FULL_NAME", mode="before")
    @classmethod
    def _coerce_bootstrap_fullname(cls, v):
        if v in ("", None):
            return "System Administrator"
        return v

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=True, extra="allow"
    )


# ----------------------------------------------------------------------------
# Sanitize environment: drop empty-string overrides for typed fields
# ----------------------------------------------------------------------------
_EMPTY_OVERRIDES = [
    "DEBUG",
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    "MAX_FAILED_LOGIN_ATTEMPTS",
    "ENABLE_BOOTSTRAP_ADMIN",
    "REDIS_PORT",
    "REDIS_DB",
    "DATABASE_URL",
    "APP_NAME",
    "APP_VERSION",
    "API_V1_PREFIX",
    "ALGORITHM",
    "BOOTSTRAP_ADMIN_USERNAME",
    "BOOTSTRAP_ADMIN_PASSWORD",
    "BOOTSTRAP_TENANT_SLUG",
    "BOOTSTRAP_TENANT_NAME",
    "BOOTSTRAP_ADMIN_EMAIL",
    "BOOTSTRAP_ADMIN_FULL_NAME",
]

for _key in _EMPTY_OVERRIDES:
    if os.getenv(_key, None) == "":
        os.environ.pop(_key, None)


_settings = Settings()


if isinstance(_settings.ALLOWED_ORIGINS, str):
    raw_origins = [origin.strip() for origin in _settings.ALLOWED_ORIGINS.split(",")]
    processed = [origin for origin in raw_origins if origin]
    _settings.ALLOWED_ORIGINS = processed or [
        "http://localhost:3000",
        "http://localhost:8000",
    ]
elif isinstance(_settings.ALLOWED_ORIGINS, list):
    processed = [origin.strip() for origin in _settings.ALLOWED_ORIGINS if origin]
    _settings.ALLOWED_ORIGINS = processed or [
        "http://localhost:3000",
        "http://localhost:8000",
    ]

settings = _settings
