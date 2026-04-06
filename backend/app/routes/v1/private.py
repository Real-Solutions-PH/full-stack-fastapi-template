from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.security import get_password_hash
from app.db.models import User
from app.repo import user_repo
from app.routes.deps import SessionDep
from app.schema.user import UserPublic

router = APIRouter(tags=["private"], prefix="/private")


class PrivateUserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    is_verified: bool = False


@router.post("/users/", response_model=UserPublic)
def create_user(user_in: PrivateUserCreate, session: SessionDep) -> Any:
    """
    Create a new user.
    """
    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
    )
    return user_repo.create(session=session, user=user)
