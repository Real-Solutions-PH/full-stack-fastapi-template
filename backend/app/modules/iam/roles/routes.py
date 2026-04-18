import uuid
from typing import Any

from fastapi import APIRouter, Depends

from app.modules.iam.deps import get_current_active_superuser
from app.modules.iam.roles import services as role_service
from app.modules.iam.roles.schema import RolePublic, RolesPublic
from app.shared.deps import SessionDep

router = APIRouter(
    prefix="/roles",
    tags=["roles"],
    dependencies=[Depends(get_current_active_superuser)],
)


@router.get("/", response_model=RolesPublic)
def read_roles(session: SessionDep, skip: int = 0, limit: int = 100) -> Any:
    roles, count = role_service.list_roles(session=session, skip=skip, limit=limit)
    return RolesPublic(
        data=[RolePublic.model_validate(r) for r in roles], count=count
    )


@router.get("/{role_id}", response_model=RolePublic)
def read_role(session: SessionDep, role_id: uuid.UUID) -> Any:
    return role_service.get_role(session=session, role_id=role_id)
