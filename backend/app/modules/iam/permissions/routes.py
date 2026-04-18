import uuid
from typing import Any

from fastapi import APIRouter, Depends

from app.modules.iam.deps import get_current_active_superuser
from app.modules.iam.permissions import services as permission_service
from app.modules.iam.permissions.schema import (
    PermissionPublic,
    PermissionsPublic,
)
from app.shared.deps import SessionDep

router = APIRouter(
    prefix="/permissions",
    tags=["permissions"],
    dependencies=[Depends(get_current_active_superuser)],
)


@router.get("/", response_model=PermissionsPublic)
def read_permissions(session: SessionDep, skip: int = 0, limit: int = 200) -> Any:
    perms, count = permission_service.list_permissions(
        session=session, skip=skip, limit=limit
    )
    return PermissionsPublic(
        data=[PermissionPublic.model_validate(p) for p in perms], count=count
    )


@router.get("/{permission_id}", response_model=PermissionPublic)
def read_permission(session: SessionDep, permission_id: uuid.UUID) -> Any:
    return permission_service.get_permission(
        session=session, permission_id=permission_id
    )
