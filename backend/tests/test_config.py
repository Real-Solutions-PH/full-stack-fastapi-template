"""Settings guardrails."""

import pytest

from app.core.config import _DEMO_SUPABASE_SERVICE_ROLE_KEY, Settings

_FERNET_KEY = "OFyzG3l-nLnfScZSkaOtDsJtK_gFkbydy4F-AJLgNHc="

_BASE: dict[str, str] = {
    "PROJECT_NAME": "t",
    "POSTGRES_SERVER": "db",
    "POSTGRES_USER": "u",
    "POSTGRES_PASSWORD": "not-default",
    "FIRST_SUPERUSER": "a@b.co",
    "FIRST_SUPERUSER_PASSWORD": "not-default",
    "CONFIG_ENCRYPTION_KEYS": _FERNET_KEY,
}


def test_demo_service_role_key_rejected_outside_local() -> None:
    with pytest.raises(ValueError, match="SUPABASE_SERVICE_ROLE_KEY"):
        Settings(
            _env_file=None,  # type: ignore[call-arg]
            ENVIRONMENT="staging",
            SUPABASE_SERVICE_ROLE_KEY=_DEMO_SUPABASE_SERVICE_ROLE_KEY,
            **_BASE,
        )


def test_demo_service_role_key_warns_in_local() -> None:
    with pytest.warns(UserWarning, match="SUPABASE_SERVICE_ROLE_KEY"):
        Settings(
            _env_file=None,  # type: ignore[call-arg]
            ENVIRONMENT="local",
            SUPABASE_SERVICE_ROLE_KEY=_DEMO_SUPABASE_SERVICE_ROLE_KEY,
            **_BASE,
        )


def test_non_demo_key_accepted_outside_local() -> None:
    s = Settings(
        _env_file=None,  # type: ignore[call-arg]
        ENVIRONMENT="staging",
        SUPABASE_SERVICE_ROLE_KEY="a-real-project-key",
        **_BASE,
    )
    assert s.SUPABASE_SERVICE_ROLE_KEY == "a-real-project-key"


def test_missing_config_encryption_key_rejected_outside_local() -> None:
    base = {**_BASE, "CONFIG_ENCRYPTION_KEYS": ""}
    with pytest.raises(ValueError, match="CONFIG_ENCRYPTION_KEYS"):
        Settings(
            _env_file=None,  # type: ignore[call-arg]
            ENVIRONMENT="staging",
            SUPABASE_SERVICE_ROLE_KEY="a-real-project-key",
            **base,
        )


def test_missing_config_encryption_key_warns_in_local() -> None:
    base = {**_BASE, "CONFIG_ENCRYPTION_KEYS": ""}
    with pytest.warns(UserWarning, match="CONFIG_ENCRYPTION_KEYS"):
        Settings(
            _env_file=None,  # type: ignore[call-arg]
            ENVIRONMENT="local",
            **base,
        )
