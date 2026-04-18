from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from pydantic.networks import EmailStr

from app.core.security import get_password_hash
from app.modules.iam.deps import get_current_active_superuser
from app.modules.iam.users import repo as user_repo
from app.modules.iam.users.models import User
from app.modules.iam.users.schema import UserPublic
from app.shared.deps import SessionDep
from app.shared.schema import Message
from app.shared.utils.email import generate_test_email, send_email

utils_router = APIRouter(prefix="/utils", tags=["utils"])


@utils_router.post(
    "/test-email/",
    dependencies=[Depends(get_current_active_superuser)],
    status_code=201,
)
def test_email(email_to: EmailStr) -> Message:
    email_data = generate_test_email(email_to=email_to)
    send_email(
        email_to=email_to,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )
    return Message(message="Test email sent")


@utils_router.get("/health-check/")
async def health_check() -> bool:
    return True


private_router = APIRouter(tags=["private"], prefix="/private")


class PrivateUserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    is_verified: bool = False


@private_router.post("/users/", response_model=UserPublic)
def create_user(user_in: PrivateUserCreate, session: SessionDep) -> Any:
    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
    )
    return user_repo.create(session=session, user=user)
