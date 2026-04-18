from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.models import User
from app.modules.iam.users import repo as user_repo
from app.modules.iam.users.schema import UserCreate
from tests.utils.utils import random_email, random_lower_string


def user_authentication_headers(
    *, client: TestClient, email: str, password: str
) -> dict[str, str]:
    data = {"username": email, "password": password}

    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=data)
    response = r.json()
    auth_token = response["access_token"]
    headers = {"Authorization": f"Bearer {auth_token}"}
    return headers


def create_random_user(db: Session) -> User:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    db_user = User.model_validate(
        user_in, update={"hashed_password": get_password_hash(user_in.password)}
    )
    user = user_repo.create(session=db, user=db_user)
    return user


def authentication_token_from_email(
    *, client: TestClient, email: str, db: Session
) -> dict[str, str]:
    """
    Return a valid token for the user with given email.

    If the user doesn't exist it is created first.
    """
    password = random_lower_string()
    user = user_repo.get_by_email(session=db, email=email)
    if not user:
        user_in_create = UserCreate(email=email, password=password)
        db_user = User.model_validate(
            user_in_create,
            update={"hashed_password": get_password_hash(user_in_create.password)},
        )
        user = user_repo.create(session=db, user=db_user)
    else:
        if not user.id:
            raise Exception("User id not set")
        hashed = get_password_hash(password)
        user = user_repo.update(
            session=db, user=user, update_data={"hashed_password": hashed}
        )

    return user_authentication_headers(client=client, email=email, password=password)
