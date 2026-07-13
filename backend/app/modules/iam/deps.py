import uuid
from collections.abc import Callable
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core import supabase_auth
from app.modules.iam.users.models import User
from app.shared.deps import SessionDep

# auto_error=False so a missing header raises OUR 401 (with WWW-Authenticate,
# preserving the prior envelope semantics) instead of HTTPBearer's 403.
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
    except jwt.exceptions.PyJWKClientConnectionError:
        # JWKS endpoint unreachable — an upstream outage, not a bad token.
        # Caught before PyJWTError (it's a subclass) so callers can retry.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        )
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    # Claims seam: stash the verified claims for downstream request handling
    # (e.g. future request.jwt.claims GUC wiring for RLS — see the runbook).
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


def require_permission(permission: str) -> Callable[..., User]:
    """Dependency factory: require ``permission`` ("resource:action").

    Superusers bypass the check (the ``is_superuser`` flag stays the
    platform-admin escape hatch); everyone else must hold the permission
    transitively via an assigned role. Use as::

        @router.get("/", dependencies=[Depends(require_permission("items:read"))])
    """

    def _dep(current_user: CurrentUser, session: SessionDep) -> User:
        if current_user.is_superuser:
            return current_user
        # Imported lazily: the rbac repo imports role/permission models whose
        # package pulls deps back through here at import time.
        from app.modules.iam.rbac import repo as rbac_repo

        held = rbac_repo.get_user_permission_names(
            session=session, user_id=current_user.id
        )
        if permission not in held:
            raise HTTPException(
                status_code=403, detail="The user doesn't have enough privileges"
            )
        return current_user

    return _dep
