import logging

from sqlalchemy import text
from sqlmodel import Session, create_engine

from app.core.config import settings

logger = logging.getLogger(__name__)

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))


def warn_if_rls_dormant() -> None:
    """Log when the app connection bypasses row-level security.

    Superusers and table owners skip RLS entirely, so the #40 policies are a
    dormant second wall until #44 flips the app engine to the non-owner
    ``app_user`` role. Non-fatal by design: purely a startup breadcrumb.
    """
    try:
        with engine.connect() as conn:
            # Table OWNERS also bypass plain ENABLE RLS — on managed Postgres
            # the app role is often a non-superuser schema owner, so checking
            # rolsuper/rolbypassrls alone gives a false all-clear.
            bypasses = conn.execute(
                text(
                    "SELECT (SELECT rolbypassrls OR rolsuper FROM pg_roles"
                    "        WHERE rolname = current_user)"
                    " OR EXISTS (SELECT 1 FROM pg_tables"
                    "            WHERE schemaname = 'public'"
                    "            AND tablename = 'item'"
                    "            AND pg_catalog.pg_has_role("
                    "                current_user, tableowner, 'MEMBER'))"
                )
            ).scalar()
            current_role = conn.execute(text("SELECT current_user")).scalar()
        if bypasses:
            logger.warning(
                "RLS is DORMANT: app connection runs as %s which bypasses row"
                " security via superuser/BYPASSRLS or table ownership"
                " (expected until #44 flips to app_user)",
                current_role,
            )
    except Exception:  # pragma: no cover - visibility only, never fatal
        logger.warning("Could not determine RLS posture of the app connection")


# Ensure every module-level SQLModel is imported (via app.db.models) before
# SQLModel resolves relationships. See:
# https://github.com/fastapi/full-stack-fastapi-template/issues/28


def init_db(session: Session) -> None:
    # Imported lazily: seeders live inside modules whose deps eventually
    # re-import ``engine`` from here, which would deadlock at module load.
    from app.core import supabase_auth
    from app.modules.iam.permissions.seed import seed_permissions
    from app.modules.iam.roles.seed import seed_roles
    from app.modules.iam.tenants import services as tenant_service
    from app.modules.iam.tenants.seed import seed_tenants
    from app.modules.iam.users import repo as user_repo
    from app.modules.iam.users.models import User
    from app.modules.items.models import Item  # noqa: F401  resolve User.items mapper

    # Tables are managed by Alembic migrations.
    # Tenants are seeded first: users (including FIRST_SUPERUSER) need one.
    seed_roles(session)
    seed_permissions(session)
    seed_tenants(session)

    # FIRST_SUPERUSER bootstrap (#39): the auth identity lives in Supabase.
    # Idempotent — create-or-fetch the GoTrue user (the password is set for
    # local/CI convenience and test fixtures), then upsert the local mirror
    # row keyed by the auth UID with is_superuser=True.
    auth_uid = supabase_auth.admin_get_or_create_user(
        email=settings.FIRST_SUPERUSER,
        password=settings.FIRST_SUPERUSER_PASSWORD,
    )
    user = session.get(User, auth_uid)
    if not user:
        user_repo.create(
            session=session,
            user=User(
                id=auth_uid,
                email=settings.FIRST_SUPERUSER,
                is_superuser=True,
                is_active=True,
                tenant_id=tenant_service.get_default_tenant(session=session).id,
            ),
        )
    elif not user.is_superuser:
        user_repo.update(session=session, user=user, update_data={"is_superuser": True})

    if settings.AI_ENABLED:
        from app.modules.ai.agents.seed import seed_agents
        from app.modules.ai.tools.seed import seed_tools

        seed_agents(session)
        seed_tools(session)
