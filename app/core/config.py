"""
Core configuration for KeneyApp.
Manages environment variables and application settings.

Includes a small guard that removes empty-string environment overrides for
typed settings (bool/int) to avoid ValidationError when a blank value is
present in the shell or .env. This lets defaults apply as intended.
"""

import os
from typing import List, Sequence, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


_TRUTHY = {"1", "true", "yes", "on"}
_FALSY = {"0", "false", "no", "off"}


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "KeneyApp"
    APP_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ENCRYPTION_KEY: str | None = None
    ENCRYPTION_SALT: str = "keneyapp-salt"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    TOKEN_ISSUER: str = "keneyapp"
    TOKEN_AUDIENCE: str = "keneyapp-clients"
    MFA_ISSUER: str = "KeneyApp"
    MAX_FAILED_LOGIN_ATTEMPTS: int = 5
    ENABLE_RATE_LIMITING: bool = True

    # Database
    DATABASE_URL: str = "postgresql://keneyapp:keneyapp@localhost:5432/keneyapp"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    DB_ECHO: bool = False

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

    # OpenTelemetry / Observability
    OTEL_ENABLED: bool = False
    OTEL_EXPORTER_TYPE: str = "console"  # "otlp", "jaeger", or "console"
    OTEL_EXPORTER_ENDPOINT: str = (
        ""  # e.g., "localhost:4317" for OTLP or "localhost:6831" for Jaeger
    )
    OTEL_SERVICE_NAME: str = "keneyapp"
    OTEL_SERVICE_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"

    # French Healthcare Integration (ANS)
    # INS (Identifiant National de Santé)
    INS_API_URL: str = ""  # ANS Teleservice INS endpoint
    INS_API_KEY: str = ""  # API key for INS verification
    INS_VALIDATION_ENABLED: bool = False  # Enable INS validation
    
    # Pro Santé Connect (PSC) - French healthcare SSO
    PSC_CLIENT_ID: str = ""
    PSC_CLIENT_SECRET: str = ""
    PSC_AUTHORIZATION_ENDPOINT: str = "https://wallet.esw.esante.gouv.fr/auth"
    PSC_TOKEN_ENDPOINT: str = "https://auth.esw.esante.gouv.fr/auth/realms/esante-wallet/protocol/openid-connect/token"
    PSC_USERINFO_ENDPOINT: str = "https://auth.esw.esante.gouv.fr/auth/realms/esante-wallet/protocol/openid-connect/userinfo"
    PSC_JWKS_URI: str = "https://auth.esw.esante.gouv.fr/auth/realms/esante-wallet/protocol/openid-connect/certs"
    PSC_SCOPE: str = "openid profile email rpps"  # RPPS = healthcare professional ID
    
    # DMP (Dossier Médical Partagé) Integration
    DMP_API_URL: str = ""  # DMP API endpoint
    DMP_API_KEY: str = ""  # API key for DMP access
    DMP_INTEGRATION_ENABLED: bool = False
    
    # MSSanté (Messagerie Sécurisée de Santé)
    MSSANTE_ENABLED: bool = False
    MSSANTE_SMTP_HOST: str = ""  # MSSanté SMTP gateway
    MSSANTE_SMTP_PORT: int = 587
    MSSANTE_USERNAME: str = ""  # MSSanté account (prenom.nom@structure.mssante.fr)
    MSSANTE_PASSWORD: str = ""
    MSSANTE_FROM_ADDRESS: str = ""

    # ------------------------------------------------------------------
    # Production safety checks
    # ------------------------------------------------------------------
    def model_post_init(self, __context: object) -> None:
        """Harden defaults when running in production.

        The application intentionally keeps sensible defaults for local
        development and automated tests. When ENVIRONMENT is set to
        "production", we enforce stricter invariants to avoid accidental
        deployments with insecure defaults.
        """

        environment = (self.ENVIRONMENT or "").lower()
        if environment != "production":
            return

        self._assert_secure_secret_key()
        self._assert_debug_disabled()
        self._assert_bootstrap_admin_disabled()
        self._assert_database_not_local()
        self._assert_allowed_origins_not_localhost()
        self._assert_encryption_key_configured()
        self._assert_token_claims_configured()

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

    @field_validator("ENABLE_RATE_LIMITING", mode="before")
    @classmethod
    def _coerce_rate_limiting(cls, v):
        if v in ("", None):
            return True
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

    @field_validator("DB_POOL_SIZE", mode="before")
    @classmethod
    def _coerce_db_pool_size(cls, v):
        if v in ("", None):
            return 10
        return v

    @field_validator("DB_MAX_OVERFLOW", mode="before")
    @classmethod
    def _coerce_db_max_overflow(cls, v):
        if v in ("", None):
            return 10
        return v

    @field_validator("DB_POOL_TIMEOUT", mode="before")
    @classmethod
    def _coerce_db_pool_timeout(cls, v):
        if v in ("", None):
            return 30
        return v

    @field_validator("DB_POOL_RECYCLE", mode="before")
    @classmethod
    def _coerce_db_pool_recycle(cls, v):
        if v in ("", None):
            return 1800
        return v

    @field_validator("DB_ECHO", mode="before")
    @classmethod
    def _coerce_db_echo(cls, v):
        if v in ("", None):
            return False
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

    @field_validator("ENCRYPTION_KEY", mode="before")
    @classmethod
    def _coerce_encryption_key(cls, v):
        if v in ("", None):
            return None
        return v

    @field_validator("ENCRYPTION_SALT", mode="before")
    @classmethod
    def _coerce_encryption_salt(cls, v):
        if v in ("", None):
            return "keneyapp-salt"
        return v

    @field_validator("TOKEN_ISSUER", mode="before")
    @classmethod
    def _coerce_token_issuer(cls, v):
        if v in ("", None):
            return "keneyapp"
        return v

    @field_validator("TOKEN_AUDIENCE", mode="before")
    @classmethod
    def _coerce_token_audience(cls, v):
        if v in ("", None):
            return "keneyapp-clients"
        return v

    @field_validator("OTEL_ENABLED", mode="before")
    @classmethod
    def _coerce_otel_enabled(cls, v):
        if v in ("", None):
            return False
        return v

    @field_validator("OTEL_EXPORTER_TYPE", mode="before")
    @classmethod
    def _coerce_otel_exporter_type(cls, v):
        if v in ("", None):
            return "console"
        return v

    @field_validator("OTEL_SERVICE_NAME", mode="before")
    @classmethod
    def _coerce_otel_service_name(cls, v):
        if v in ("", None):
            return "keneyapp"
        return v

    @field_validator("OTEL_SERVICE_VERSION", mode="before")
    @classmethod
    def _coerce_otel_service_version(cls, v):
        if v in ("", None):
            return "1.0.0"
        return v

    @field_validator("ENVIRONMENT", mode="before")
    @classmethod
    def _coerce_environment(cls, v):
        if v in ("", None):
            return "development"
        return v

    # ------------------------------------------------------------------
    # Production assertions
    # ------------------------------------------------------------------
    def _assert_secure_secret_key(self) -> None:
        if self.SECRET_KEY == "your-secret-key-change-in-production":
            raise ValueError("SECRET_KEY must be set for production deployments.")
        if len(self.SECRET_KEY) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters long in production."
            )

    def _assert_debug_disabled(self) -> None:
        if self.DEBUG:
            raise ValueError("DEBUG must be disabled in production.")

    def _assert_bootstrap_admin_disabled(self) -> None:
        if not self.ENABLE_BOOTSTRAP_ADMIN:
            return

        if (
            self.BOOTSTRAP_ADMIN_USERNAME == "admin"
            or self.BOOTSTRAP_ADMIN_PASSWORD == "admin123"
        ):
            raise ValueError(
                "Disable bootstrap admin or change the default credentials before deploying to production."
            )

    def _assert_database_not_local(self) -> None:
        if self.DATABASE_URL.startswith("postgresql://keneyapp:keneyapp@localhost"):
            raise ValueError(
                "DATABASE_URL must point to a production database when ENVIRONMENT=production."
            )

    def _assert_allowed_origins_not_localhost(self) -> None:
        origins = self._normalized_origins(self.ALLOWED_ORIGINS)
        if not origins:
            raise ValueError(
                "ALLOWED_ORIGINS must be configured for production deployments."
            )

        if all(
            origin.startswith(("http://localhost", "http://127.0.0.1"))
            for origin in origins
        ):
            raise ValueError(
                "ALLOWED_ORIGINS cannot be limited to localhost values in production."
            )

        self.ALLOWED_ORIGINS = origins

    def _assert_encryption_key_configured(self) -> None:
        if not self.ENCRYPTION_KEY:
            raise ValueError(
                "ENCRYPTION_KEY must be configured for production deployments."
            )

        if len(self.ENCRYPTION_KEY) < 32:
            raise ValueError("ENCRYPTION_KEY must be at least 32 characters long.")

    def _assert_token_claims_configured(self) -> None:
        if not self.TOKEN_ISSUER:
            raise ValueError("TOKEN_ISSUER must be set for production deployments.")

        if not self.TOKEN_AUDIENCE:
            raise ValueError("TOKEN_AUDIENCE must be set for production deployments.")

    @staticmethod
    def _normalized_origins(origins: Union[str, Sequence[str]]) -> List[str]:
        if isinstance(origins, str):
            parsed = [origin.strip() for origin in origins.split(",")]
        else:
            parsed = [origin.strip() for origin in origins]

        return [origin for origin in parsed if origin]

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=True, extra="allow"
    )


# ----------------------------------------------------------------------------
# Sanitize environment: drop empty-string overrides for typed fields and
# remove invalid boolean values so defaults can apply.
# ----------------------------------------------------------------------------
_EMPTY_OVERRIDES = [
    "DEBUG",
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    "MAX_FAILED_LOGIN_ATTEMPTS",
    "ENABLE_RATE_LIMITING",
    "ENABLE_BOOTSTRAP_ADMIN",
    "REDIS_PORT",
    "REDIS_DB",
    "DATABASE_URL",
    "DB_POOL_SIZE",
    "DB_MAX_OVERFLOW",
    "DB_POOL_TIMEOUT",
    "DB_POOL_RECYCLE",
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
    "ENCRYPTION_KEY",
    "ENCRYPTION_SALT",
    "TOKEN_ISSUER",
    "TOKEN_AUDIENCE",
    "OTEL_ENABLED",
    "OTEL_EXPORTER_TYPE",
    "OTEL_SERVICE_NAME",
    "OTEL_SERVICE_VERSION",
    "ENVIRONMENT",
]
_BOOL_OVERRIDES = {
    "DEBUG",
    "ENABLE_RATE_LIMITING",
    "ENABLE_BOOTSTRAP_ADMIN",
    "OTEL_ENABLED",
    "DB_ECHO",
}

for _key in _BOOL_OVERRIDES:
    raw_value = os.getenv(_key, None)
    if raw_value is None:
        continue

    normalized = str(raw_value).strip().lower()
    if normalized in _TRUTHY | _FALSY:
        continue

    os.environ.pop(_key, None)

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


def _has_local_origin(origins: List[str]) -> bool:
    """Return True if any origin points to localhost or loopback."""

    local_prefixes = (
        "http://localhost",
        "https://localhost",
        "http://127.0.0.1",
        "https://127.0.0.1",
    )
    return any(origin.startswith(local_prefixes) for origin in origins)


def validate_production_settings(current_settings: Settings) -> None:
    """Ensure critical settings are hardened when running in production.

    The application aborts startup if any high-risk misconfigurations are
    detected. This prevents accidental deployments with debug mode enabled,
    weak secrets, or localhost-only origins.
    """

    if str(current_settings.ENVIRONMENT).lower() != "production":
        return

    issues: List[str] = []

    if (
        not current_settings.SECRET_KEY
        or current_settings.SECRET_KEY == "your-secret-key-change-in-production"
    ):
        issues.append(
            "SECRET_KEY must be set to a strong, non-default value in production."
        )

    if current_settings.DEBUG:
        issues.append("DEBUG must be disabled in production.")

    if not current_settings.ALLOWED_ORIGINS:
        issues.append("ALLOWED_ORIGINS must include at least one trusted origin.")
    elif _has_local_origin(current_settings.ALLOWED_ORIGINS):
        issues.append(
            "ALLOWED_ORIGINS cannot include localhost or loopback origins in production."
        )

    if "localhost" in str(current_settings.DATABASE_URL):
        issues.append(
            "DATABASE_URL must point to a production database host (not localhost)."
        )

    if current_settings.ACCESS_TOKEN_EXPIRE_MINUTES <= 0:
        issues.append("ACCESS_TOKEN_EXPIRE_MINUTES must be a positive integer.")

    if not current_settings.ENCRYPTION_KEY:
        issues.append("ENCRYPTION_KEY must be provided for production deployments.")
    elif len(current_settings.ENCRYPTION_KEY) < 32:
        issues.append(
            "ENCRYPTION_KEY must be at least 32 characters long in production."
        )

    if not current_settings.TOKEN_ISSUER:
        issues.append("TOKEN_ISSUER must be configured for production deployments.")

    if not current_settings.TOKEN_AUDIENCE:
        issues.append("TOKEN_AUDIENCE must be configured for production deployments.")

    if issues:
        raise RuntimeError(
            "Production configuration validation failed: " + "; ".join(issues)
        )


def _coerce_bool_env(value: str | None, default: bool) -> bool:
    """Parse a boolean-like environment value with sensible fallbacks.

    This mirrors common environment parsing while still allowing defaults to
    apply when a value is missing or invalid.
    """

    if value is None:
        return default

    normalized = str(value).strip().lower()
    if normalized in _TRUTHY:
        return True
    if normalized in _FALSY:
        return False
    return default


def is_rate_limiting_enabled() -> bool:
    """Return whether rate limiting should be enabled for the current process.

    Priority is given to the raw environment variable to keep runtime overrides
    (e.g., in tests) working even if the Settings instance was created earlier.
    Invalid or blank values fall back to the configured default.
    """

    return _coerce_bool_env(
        os.getenv("ENABLE_RATE_LIMITING"), settings.ENABLE_RATE_LIMITING
    )
