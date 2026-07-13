from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.core.config import settings
from app.core.db import engine, init_db
from app.db.models import Item, User
from app.main import app
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import get_superuser_token_headers


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session, None, None]:
    # init_db needs the local Supabase stack running (make supabase-up):
    # the FIRST_SUPERUSER bootstrap goes through the GoTrue admin API.
    with Session(engine) as session:
        init_db(session)
        yield session
        # Local rows only — GoTrue users persist across runs, which is why
        # every fixture-side create is idempotent.
        statement = delete(Item)
        session.execute(statement)
        statement = delete(User)
        session.execute(statement)
        session.commit()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def superuser_token_headers() -> dict[str, str]:
    return get_superuser_token_headers()


@pytest.fixture(scope="module")
def normal_user_token_headers(db: Session) -> dict[str, str]:
    return authentication_token_from_email(email=settings.EMAIL_TEST_USER, db=db)
