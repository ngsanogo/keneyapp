import pytest

from app.core.config import Settings


def test_enforce_production_allows_secure_configuration():
    settings = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="super-secret-key",
        DEBUG=False,
        ALLOWED_ORIGINS=["https://keneyapp.example"],
    )

    settings.enforce_production_safety()


@pytest.mark.parametrize(
    "kwargs, expected_error",
    [
        (
            {"ENVIRONMENT": "production", "SECRET_KEY": "your-secret-key-change-in-production", "DEBUG": False},
            "SECRET_KEY must be overridden in production",
        ),
        (
            {"ENVIRONMENT": "production", "DEBUG": True, "ALLOWED_ORIGINS": ["https://keneyapp.example"]},
            "DEBUG must be False in production",
        ),
        (
            {"ENVIRONMENT": "production", "ALLOWED_ORIGINS": ["*"]},
            "ALLOWED_ORIGINS cannot include '*' in production",
        ),
        (
            {"ENVIRONMENT": "production", "ALLOWED_ORIGINS": []},
            "ALLOWED_ORIGINS must include at least one origin in production",
        ),
    ],
)
def test_enforce_production_raises_on_insecure_defaults(kwargs, expected_error):
    settings = Settings(**kwargs)

    with pytest.raises(ValueError) as exc_info:
        settings.enforce_production_safety()

    assert expected_error in str(exc_info.value)
