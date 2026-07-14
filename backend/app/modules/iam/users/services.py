import uuid

import httpx
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
    try:
        auth_uid = supabase_auth.admin_get_or_create_user(
            email=user_in.email, adopt_existing=False
        )
    except supabase_auth.EmailExistsError:
        raise HTTPException(
            status_code=409,
            detail=(
                "email already registered with the auth provider — "
                "verify ownership before granting access"
            ),
        )
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

    Before creating anything, the auth identity is re-checked against
    GoTrue: a deleted user's access token stays signature-valid until
    ``exp``, and without this check it would silently resurrect the
    account (local row re-created from stale claims).
    """
    if not supabase_auth.admin_user_exists(user_id):
        raise HTTPException(status_code=401, detail="Auth user no longer exists")
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


def _sync_email_to_gotrue(*, user: User, new_email: str | None) -> None:
    """Propagate a local email change to the GoTrue identity.

    Called BEFORE the local commit: if GoTrue rejects the change the local
    row is left untouched and the request fails with a 502 envelope, so the
    two stores can't drift apart.
    """
    if not new_email or new_email == user.email:
        return
    try:
        supabase_auth.admin_update_email(user.id, new_email)
    except httpx.HTTPError:
        raise HTTPException(
            status_code=502,
            detail="Failed to update the email with the auth provider",
        )


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
    _sync_email_to_gotrue(user=db_user, new_email=user_in.email)
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
    _sync_email_to_gotrue(user=current_user, new_email=user_in.email)
    update_data = user_in.model_dump(exclude_unset=True)
    return user_repo.update(session=session, user=current_user, update_data=update_data)


def _revoke_gotrue_identity(user_id: uuid.UUID) -> None:
    """Revoke the GoTrue identity BEFORE the local row is deleted/committed.

    Mirrors ``_sync_email_to_gotrue``: call GoTrue first so a provider
    failure aborts the request (502 envelope) with the local row and its
    data untouched, instead of leaving a half-deleted account whose live
    auth identity would JIT-resurrect an empty row on the next request.
    ``admin_delete_user`` already tolerates an already-gone identity
    (GoTrue 404), so re-revoking is a safe no-op.
    """
    try:
        supabase_auth.admin_delete_user(user_id)
    except httpx.HTTPError:
        raise HTTPException(
            status_code=502,
            detail="Failed to delete the user with the auth provider",
        )


def delete_user_me(*, session: Session, current_user: User) -> None:
    if current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="Super users are not allowed to delete themselves",
        )
    _revoke_gotrue_identity(current_user.id)
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
    _revoke_gotrue_identity(user_id)
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
