import uuid
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core import supabase_auth
from app.modules.iam.users.models import User
from app.shared.deps import SessionDep

# auto_error=False so a missing header raises OUR 401 (with WWW-Authenticate,
# preserving the pre-#39 envelope semantics) instead of HTTPBearer's 403.
bearer_scheme = HTTPBearer(auto_error=False)


def get_bearer_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> str:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


TokenDep = Annotated[str, Depends(get_bearer_token)]


def get_current_user(request: Request, session: SessionDep, token: TokenDep) -> User:
    try:
        claims = supabase_auth.verify_token(token)
        user_id = uuid.UUID(str(claims["sub"]))
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    # Claims seam: stash the verified claims for downstream request handling
    # (e.g. future request.jwt.claims GUC wiring for RLS — see #40 runbook).
    request.state.jwt_claims = claims
    user = session.get(User, user_id)
    if not user:
        # JIT provisioning: the Supabase auth UID is the local PK; first
        # sight of a valid token creates the mirror row.
        from app.modules.iam.users import services as user_service

        email = claims.get("email")
        if not email:
            raise HTTPException(status_code=403, detail="Token has no email claim")
        user = user_service.provision_user_from_claims(
            session=session, user_id=user_id, email=str(email)
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_active_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user
