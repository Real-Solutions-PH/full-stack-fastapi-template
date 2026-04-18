from sqlmodel import Session, create_engine, select

from app.core.config import settings
from app.core.security import get_password_hash

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))


# Ensure every module-level SQLModel is imported (via app.db.models) before
# SQLModel resolves relationships. See:
# https://github.com/fastapi/full-stack-fastapi-template/issues/28


def init_db(session: Session) -> None:
    # Imported lazily: seeders live inside modules whose deps eventually
    # re-import ``engine`` from here, which would deadlock at module load.
    from app.modules.iam.permissions.seed import seed_permissions
    from app.modules.iam.roles.seed import seed_roles
    from app.modules.iam.tenants.seed import seed_tenants
    from app.modules.iam.users import repo as user_repo
    from app.modules.iam.users.models import User
    from app.modules.iam.users.schema import UserCreate

    # Tables are managed by Alembic migrations.
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
            user_in, update={"hashed_password": get_password_hash(user_in.password)}
        )
        user_repo.create(session=session, user=db_user)

    seed_roles(session)
    seed_permissions(session)
    seed_tenants(session)
