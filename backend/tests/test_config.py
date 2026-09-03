"""Settings guardrails."""

import pytest

from app.core.config import _DEMO_SUPABASE_SERVICE_ROLE_KEY, Settings

_BASE: dict[str, str] = {
    "PROJECT_NAME": "t",
    "POSTGRES_SERVER": "db",
    "POSTGRES_USER": "u",
    "POSTGRES_PASSWORD": "not-default",
    "FIRST_SUPERUSER": "a@b.co",
    "FIRST_SUPERUSER_PASSWORD": "not-default",
    # Non-default object-store creds so the deployment-secret guard passes;
    # individual MinIO tests override these back to a known-insecure value.
    "MINIO_ROOT_USER": "real-access-key",
    "MINIO_ROOT_PASSWORD": "real-secret-key",
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


@pytest.mark.parametrize("bad", ["minioadmin", "changethis"])
def test_minio_root_password_default_rejected_outside_local(bad: str) -> None:
    with pytest.raises(ValueError, match="MINIO_ROOT_PASSWORD"):
        Settings(
            _env_file=None,  # type: ignore[call-arg]
            ENVIRONMENT="production",
            SUPABASE_SERVICE_ROLE_KEY="a-real-project-key",
            **{**_BASE, "MINIO_ROOT_PASSWORD": bad},
        )


def test_minio_root_user_default_rejected_outside_local() -> None:
    with pytest.raises(ValueError, match="MINIO_ROOT_USER"):
        Settings(
            _env_file=None,  # type: ignore[call-arg]
            ENVIRONMENT="production",
            SUPABASE_SERVICE_ROLE_KEY="a-real-project-key",
            **{**_BASE, "MINIO_ROOT_USER": "minioadmin"},
        )


def test_minio_defaults_only_warn_in_local() -> None:
    with pytest.warns(UserWarning, match="MINIO_ROOT_PASSWORD"):
        Settings(
            _env_file=None,  # type: ignore[call-arg]
            ENVIRONMENT="local",
            **{**_BASE, "MINIO_ROOT_USER": "minioadmin", "MINIO_ROOT_PASSWORD": "minioadmin"},
        )


def test_empty_service_role_key_rejected_outside_local() -> None:
    with pytest.raises(ValueError, match="SUPABASE_SERVICE_ROLE_KEY"):
        Settings(
            _env_file=None,  # type: ignore[call-arg]
            ENVIRONMENT="staging",
            **{**_BASE, "SUPABASE_SERVICE_ROLE_KEY": ""},
        )


def test_empty_service_role_key_allowed_in_local() -> None:
    s = Settings(
        _env_file=None,  # type: ignore[call-arg]
        ENVIRONMENT="local",
        **{**_BASE, "SUPABASE_SERVICE_ROLE_KEY": ""},
    )
    assert s.SUPABASE_SERVICE_ROLE_KEY == ""
