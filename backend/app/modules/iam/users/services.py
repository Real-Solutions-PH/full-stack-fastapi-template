import uuid

from fastapi import HTTPException
from sqlmodel import Session

from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.modules.iam.users import repo as user_repo
from app.modules.iam.users.models import User
from app.modules.iam.users.schema import (
    UpdatePassword,
    UserCreate,
    UserRegister,
    UserUpdate,
    UserUpdateMe,
)
from app.shared.utils.email import send_email
from app.modules.iam.auth.utils import generate_new_account_email


def list_users(
    *, session: Session, skip: int = 0, limit: int = 100
) -> tuple[list[User], int]:
    return user_repo.get_multi(session=session, skip=skip, limit=limit)


def get_user_by_id(*, session: Session, user_id: uuid.UUID) -> User | None:
    return user_repo.get_by_id(session=session, user_id=user_id)


def create_user(*, session: Session, user_in: UserCreate) -> User:
    existing = user_repo.get_by_email(session=session, email=user_in.email)
    if existing:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    db_user = User.model_validate(
        user_in, update={"hashed_password": get_password_hash(user_in.password)}
    )
    user = user_repo.create(session=session, user=db_user)
    if settings.emails_enabled and user_in.email:
        email_data = generate_new_account_email(
            email_to=user_in.email, username=user_in.email, password=user_in.password
        )
        send_email(
            email_to=user_in.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    return user


def register_user(*, session: Session, user_in: UserRegister) -> User:
    existing = user_repo.get_by_email(session=session, email=user_in.email)
    if existing:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )
    user_create = UserCreate.model_validate(user_in)
    db_user = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    return user_repo.create(session=session, user=db_user)


def update_user(
    *, session: Session, user_id: uuid.UUID, user_in: UserUpdate
) -> User:
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
    extra_data = {}
    if "password" in user_data:
        password = user_data.pop("password")
        extra_data["hashed_password"] = get_password_hash(password)
    update_data = {**user_data, **extra_data}
    return user_repo.update(session=session, user=db_user, update_data=update_data)


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
    return user_repo.update(
        session=session, user=current_user, update_data=update_data
    )


def update_password_me(
    *, session: Session, current_user: User, body: UpdatePassword
) -> None:
    verified, _ = verify_password(body.current_password, current_user.hashed_password)
    if not verified:
        raise HTTPException(status_code=400, detail="Incorrect password")
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=400,
            detail="New password cannot be the same as the current one",
        )
    hashed = get_password_hash(body.new_password)
    user_repo.update(
        session=session, user=current_user, update_data={"hashed_password": hashed}
    )


def delete_user_me(*, session: Session, current_user: User) -> None:
    if current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="Super users are not allowed to delete themselves",
        )
    user_repo.delete_user(session=session, user=current_user)


def delete_user(
    *, session: Session, current_user: User, user_id: uuid.UUID
) -> None:
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
