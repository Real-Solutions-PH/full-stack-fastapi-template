from datetime import timedelta

from fastapi import HTTPException
from sqlmodel import Session

from app.core import security
from app.core.config import settings
from app.modules.iam.auth.schema import NewPassword, Token
from app.modules.iam.auth.utils import (
    generate_password_reset_token,
    generate_reset_password_email,
    verify_password_reset_token,
)
from app.modules.iam.users import repo as user_repo
from app.shared.utils.email import send_email


def login(*, session: Session, email: str, password: str) -> Token:
    user = user_repo.authenticate(session=session, email=email, password=password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return Token(
        access_token=security.create_access_token(
            user.id, expires_delta=access_token_expires
        )
    )


def recover_password(*, session: Session, email: str) -> None:
    user = user_repo.get_by_email(session=session, email=email)
    if user:
        password_reset_token = generate_password_reset_token(email=email)
        email_data = generate_reset_password_email(
            email_to=user.email, email=email, token=password_reset_token
        )
        send_email(
            email_to=user.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )


def reset_password(*, session: Session, body: NewPassword) -> None:
    email = verify_password_reset_token(token=body.token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token")
    user = user_repo.get_by_email(session=session, email=email)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    hashed = security.get_password_hash(body.new_password)
    user_repo.update(
        session=session, user=user, update_data={"hashed_password": hashed}
    )
