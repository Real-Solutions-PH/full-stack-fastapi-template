import uuid
from typing import Any

from sqlmodel import Session, col, delete, func, select

from app.core.security import verify_password
from app.modules.iam.users.models import User

# Dummy Argon2 hash for constant-time auth failures (timing-attack mitigation).
DUMMY_HASH = "$argon2id$v=19$m=65536,t=3,p=4$MjQyZWE1MzBjYjJlZTI0Yw$YTU4NGM5ZTZmYjE2NzZlZjY0ZWY3ZGRkY2U2OWFjNjk"


def get_by_id(*, session: Session, user_id: uuid.UUID) -> User | None:
    return session.get(User, user_id)


def get_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()


def get_multi(
    *, session: Session, skip: int = 0, limit: int = 100
) -> tuple[list[User], int]:
    count = session.exec(select(func.count()).select_from(User)).one()
    users = session.exec(
        select(User).order_by(col(User.created_at).desc()).offset(skip).limit(limit)
    ).all()
    return list(users), count


def create(*, session: Session, user: User) -> User:
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def update(*, session: Session, user: User, update_data: dict[str, Any]) -> User:
    user.sqlmodel_update(update_data)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def delete_user(*, session: Session, user: User) -> None:
    session.delete(user)
    session.commit()


def delete_user_cascade(*, session: Session, user: User) -> None:
    from app.modules.items.models import Item

    statement = delete(Item).where(col(Item.owner_id) == user.id)
    session.exec(statement)
    session.delete(user)
    session.commit()


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    db_user = get_by_email(session=session, email=email)
    if not db_user:
        verify_password(password, DUMMY_HASH)
        return None
    verified, updated_password_hash = verify_password(
        password, db_user.hashed_password
    )
    if not verified:
        return None
    if updated_password_hash:
        db_user.hashed_password = updated_password_hash
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
    return db_user
