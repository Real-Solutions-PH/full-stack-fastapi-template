import uuid

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.core import supabase_auth
from app.modules.iam.tenants import services as tenant_service
from app.modules.iam.users import repo as user_repo
from app.modules.iam.users.models import User
from app.modules.iam.users.schema import (
    UserCreate,
    UserUpdate,
    UserUpdateMe,
)


def list_users(
    *, session: Session, skip: int = 0, limit: int = 100
) -> tuple[list[User], int]:
    return user_repo.get_multi(session=session, skip=skip, limit=limit)


def get_user_by_id(*, session: Session, user_id: uuid.UUID) -> User | None:
    return user_repo.get_by_id(session=session, user_id=user_id)


def create_user(*, session: Session, user_in: UserCreate) -> User:
    """Superuser-driven creation: GoTrue admin user + mirrored local row.

    The auth user is created without a password (email confirmed); the
    person signs in via Supabase recovery / magic link.
    """
    existing = user_repo.get_by_email(session=session, email=user_in.email)
    if existing:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    auth_uid = supabase_auth.admin_get_or_create_user(email=user_in.email)
    tenant = tenant_service.get_default_tenant(session=session)
    db_user = User.model_validate(
        user_in, update={"id": auth_uid, "tenant_id": tenant.id}
    )
    return user_repo.create(session=session, user=db_user)


def provision_user_from_claims(
    *, session: Session, user_id: uuid.UUID, email: str
) -> User:
    """JIT-provision the local mirror row for a verified Supabase token.

    Race-safe: a concurrent insert of the same id loses the unique check,
    rolls back, and re-reads the winner's row.
    """
    tenant = tenant_service.get_default_tenant(session=session)
    user = User(id=user_id, email=email, is_active=True, tenant_id=tenant.id)
    session.add(user)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        existing = user_repo.get_by_id(session=session, user_id=user_id)
        if existing is None:
            # Same email under a different id — stale pre-Supabase row.
            raise HTTPException(
                status_code=409,
                detail="A user with this email already exists under another id",
            )
        return existing
    session.refresh(user)
    return user


def update_user(*, session: Session, user_id: uuid.UUID, user_in: UserUpdate) -> User:
    db_user = user_repo.get_by_id(session=session, user_id=user_id)
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )
    if user_in.email:
        existing = user_repo.get_by_email(session=session, email=user_in.email)
        if existing and existing.id != user_id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )
    user_data = user_in.model_dump(exclude_unset=True)
    return user_repo.update(session=session, user=db_user, update_data=user_data)


def update_user_me(
    *, session: Session, current_user: User, user_in: UserUpdateMe
) -> User:
    if user_in.email:
        existing = user_repo.get_by_email(session=session, email=user_in.email)
        if existing and existing.id != current_user.id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )
    update_data = user_in.model_dump(exclude_unset=True)
    return user_repo.update(session=session, user=current_user, update_data=update_data)


def delete_user_me(*, session: Session, current_user: User) -> None:
    if current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="Super users are not allowed to delete themselves",
        )
    user_repo.delete_user(session=session, user=current_user)


def delete_user(*, session: Session, current_user: User, user_id: uuid.UUID) -> None:
    user = user_repo.get_by_id(session=session, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user == current_user:
        raise HTTPException(
            status_code=403,
            detail="Super users are not allowed to delete themselves",
        )
    user_repo.delete_user_cascade(session=session, user=user)


def read_user_by_id(
    *, session: Session, user_id: uuid.UUID, current_user: User
) -> User:
    user = user_repo.get_by_id(session=session, user_id=user_id)
    if user == current_user:
        return user
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="The user doesn't have enough privileges",
        )
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user
