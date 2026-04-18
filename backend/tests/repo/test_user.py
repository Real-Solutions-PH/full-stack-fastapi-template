from fastapi.encoders import jsonable_encoder
from pwdlib.hashers.bcrypt import BcryptHasher
from sqlmodel import Session

from app.core.security import get_password_hash, verify_password
from app.db.models import User
from app.modules.iam.users import repo as user_repo
from app.modules.iam.users.schema import UserCreate
from tests.utils.utils import random_email, random_lower_string


def _create_user(db: Session, user_in: UserCreate) -> User:
    """Helper to create a user from a UserCreate schema via the repo layer."""
    db_user = User.model_validate(
        user_in, update={"hashed_password": get_password_hash(user_in.password)}
    )
    return user_repo.create(session=db, user=db_user)


def test_create_user(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = _create_user(db, user_in)
    assert user.email == email
    assert hasattr(user, "hashed_password")


def test_authenticate_user(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = _create_user(db, user_in)
    authenticated_user = user_repo.authenticate(
        session=db, email=email, password=password
    )
    assert authenticated_user
    assert user.email == authenticated_user.email


def test_not_authenticate_user(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user = user_repo.authenticate(session=db, email=email, password=password)
    assert user is None


def test_check_if_user_is_active(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = _create_user(db, user_in)
    assert user.is_active is True


def test_check_if_user_is_active_inactive(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, is_active=False)
    user = _create_user(db, user_in)
    assert user.is_active is False


def test_check_if_user_is_superuser(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, is_superuser=True)
    user = _create_user(db, user_in)
    assert user.is_superuser is True


def test_check_if_user_is_superuser_normal_user(db: Session) -> None:
    username = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=username, password=password)
    user = _create_user(db, user_in)
    assert user.is_superuser is False


def test_get_user(db: Session) -> None:
    password = random_lower_string()
    username = random_email()
    user_in = UserCreate(email=username, password=password, is_superuser=True)
    user = _create_user(db, user_in)
    user_2 = user_repo.get_by_id(session=db, user_id=user.id)
    assert user_2
    assert user.email == user_2.email
    assert jsonable_encoder(user) == jsonable_encoder(user_2)


def test_update_user(db: Session) -> None:
    password = random_lower_string()
    email = random_email()
    user_in = UserCreate(email=email, password=password, is_superuser=True)
    user = _create_user(db, user_in)
    new_password = random_lower_string()
    if user.id is not None:
        hashed = get_password_hash(new_password)
        user_repo.update(
            session=db, user=user, update_data={"hashed_password": hashed}
        )
    user_2 = user_repo.get_by_id(session=db, user_id=user.id)
    assert user_2
    assert user.email == user_2.email
    verified, _ = verify_password(new_password, user_2.hashed_password)
    assert verified


def test_authenticate_user_with_bcrypt_upgrades_to_argon2(db: Session) -> None:
    """Test that a user with bcrypt password hash gets upgraded to argon2 on login."""
    email = random_email()
    password = random_lower_string()

    # Create a bcrypt hash directly (simulating legacy password)
    bcrypt_hasher = BcryptHasher()
    bcrypt_hash = bcrypt_hasher.hash(password)
    assert bcrypt_hash.startswith("$2")  # bcrypt hashes start with $2

    # Create user with bcrypt hash directly in the database
    user = User(email=email, hashed_password=bcrypt_hash)
    user_repo.create(session=db, user=user)

    # Verify the hash is bcrypt before authentication
    assert user.hashed_password.startswith("$2")

    # Authenticate - this should upgrade the hash to argon2
    authenticated_user = user_repo.authenticate(
        session=db, email=email, password=password
    )
    assert authenticated_user
    assert authenticated_user.email == email

    db.refresh(authenticated_user)

    # Verify the hash was upgraded to argon2
    assert authenticated_user.hashed_password.startswith("$argon2")

    verified, updated_hash = verify_password(
        password, authenticated_user.hashed_password
    )
    assert verified
    # Should not need another update since it's already argon2
    assert updated_hash is None
