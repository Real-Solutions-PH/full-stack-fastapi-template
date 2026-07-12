import logging

from sqlalchemy import text
from sqlmodel import Session, create_engine, select

from app.core.config import settings
from app.core.security import get_password_hash

logger = logging.getLogger(__name__)

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))


def warn_if_rls_dormant() -> None:
    """Log when the app connection bypasses row-level security.

    Superusers and table owners skip RLS entirely, so the #40 policies are a
    dormant second wall until #39 flips the app engine to the non-owner
    ``app_user`` role. Non-fatal by design: purely a startup breadcrumb.
    """
    try:
        with engine.connect() as conn:
            bypasses = conn.execute(
                text(
                    "SELECT rolbypassrls OR rolsuper FROM pg_roles"
                    " WHERE rolname = current_user"
                )
            ).scalar()
        if bypasses:
            logger.warning(
                "RLS is DORMANT: app connection runs as %s which bypasses row"
                " security (expected until #39 flips to app_user)",
                settings.POSTGRES_USER,
            )
    except Exception:  # pragma: no cover - visibility only, never fatal
        logger.warning("Could not determine RLS posture of the app connection")


# Ensure every module-level SQLModel is imported (via app.db.models) before
# SQLModel resolves relationships. See:
# https://github.com/fastapi/full-stack-fastapi-template/issues/28


def init_db(session: Session) -> None:
    # Imported lazily: seeders live inside modules whose deps eventually
    # re-import ``engine`` from here, which would deadlock at module load.
    from app.modules.iam.permissions.seed import seed_permissions
    from app.modules.iam.roles.seed import seed_roles
    from app.modules.iam.tenants import services as tenant_service
    from app.modules.iam.tenants.seed import seed_tenants
    from app.modules.iam.users import repo as user_repo
    from app.modules.iam.users.models import User
    from app.modules.iam.users.schema import UserCreate
    from app.modules.items.models import Item  # noqa: F401  resolve User.items mapper

    # Tables are managed by Alembic migrations.
    # Tenants are seeded first: users (including FIRST_SUPERUSER) need one.
    seed_roles(session)
    seed_permissions(session)
    seed_tenants(session)

    user = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        db_user = User.model_validate(
            user_in,
            update={
                "hashed_password": get_password_hash(user_in.password),
                "tenant_id": tenant_service.get_default_tenant(session=session).id,
            },
        )
        user_repo.create(session=session, user=db_user)

    if settings.AI_ENABLED:
        from app.modules.ai.agents.seed import seed_agents
        from app.modules.ai.tools.seed import seed_tools

        seed_agents(session)
        seed_tools(session)
