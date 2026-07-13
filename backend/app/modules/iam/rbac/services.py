import uuid

from fastapi import HTTPException
from sqlmodel import Session

from app.modules.iam.permissions import repo as permission_repo
from app.modules.iam.permissions.schema import PermissionPublic
from app.modules.iam.rbac import repo as rbac_repo
from app.modules.iam.rbac.schema import UserPermissions
from app.modules.iam.roles import repo as role_repo
from app.modules.iam.roles.schema import RolePublic
from app.modules.iam.users import repo as user_repo


def _require_user(session: Session, user_id: uuid.UUID) -> None:
    if user_repo.get_by_id(session=session, user_id=user_id) is None:
        raise HTTPException(status_code=404, detail="User not found")


def _require_role(session: Session, role_id: uuid.UUID) -> None:
    if role_repo.get_by_id(session=session, role_id=role_id) is None:
        raise HTTPException(status_code=404, detail="Role not found")


def _require_permission(session: Session, permission_id: uuid.UUID) -> None:
    if permission_repo.get_by_id(session=session, permission_id=permission_id) is None:
        raise HTTPException(status_code=404, detail="Permission not found")


def assign_role_to_user(
    *, session: Session, user_id: uuid.UUID, role_id: uuid.UUID
) -> None:
    _require_user(session, user_id)
    _require_role(session, role_id)
    rbac_repo.assign_role_to_user(session=session, user_id=user_id, role_id=role_id)


def remove_role_from_user(
    *, session: Session, user_id: uuid.UUID, role_id: uuid.UUID
) -> None:
    _require_user(session, user_id)
    _require_role(session, role_id)
    rbac_repo.remove_role_from_user(session=session, user_id=user_id, role_id=role_id)


def add_permission_to_role(
    *, session: Session, role_id: uuid.UUID, permission_id: uuid.UUID
) -> None:
    _require_role(session, role_id)
    _require_permission(session, permission_id)
    rbac_repo.add_permission_to_role(
        session=session, role_id=role_id, permission_id=permission_id
    )


def remove_permission_from_role(
    *, session: Session, role_id: uuid.UUID, permission_id: uuid.UUID
) -> None:
    _require_role(session, role_id)
    _require_permission(session, permission_id)
    rbac_repo.remove_permission_from_role(
        session=session, role_id=role_id, permission_id=permission_id
    )


def get_user_permissions(*, session: Session, user_id: uuid.UUID) -> UserPermissions:
    _require_user(session, user_id)
    roles = rbac_repo.get_user_roles(session=session, user_id=user_id)
    # Deduplicate permissions across roles, keyed by permission id.
    seen: dict[uuid.UUID, PermissionPublic] = {}
    for role in roles:
        for perm in rbac_repo.get_role_permissions(session=session, role_id=role.id):
            seen.setdefault(perm.id, PermissionPublic.model_validate(perm))
    return UserPermissions(
        roles=[RolePublic.model_validate(r) for r in roles],
        permissions=list(seen.values()),
    )
