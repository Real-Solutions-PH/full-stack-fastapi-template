from sqlmodel import Session

from app.modules.iam.permissions import repo as permission_repo
from app.modules.iam.permissions.models import Permission

# (resource, action, description)
DEFAULT_PERMISSIONS: list[tuple[str, str, str]] = [
    ("users", "read", "Read user records"),
    ("users", "write", "Create or update user records"),
    ("users", "delete", "Delete user records"),
    ("items", "read", "Read items"),
    ("items", "write", "Create or update items"),
    ("items", "delete", "Delete items"),
    ("roles", "read", "Read role definitions"),
    ("permissions", "read", "Read permission definitions"),
    ("tenants", "read", "Read tenant records"),
]


def seed_permissions(session: Session) -> None:
    for resource, action, description in DEFAULT_PERMISSIONS:
        name = f"{resource}:{action}"
        if permission_repo.get_by_name(session=session, name=name) is None:
            permission_repo.create(
                session=session,
                permission=Permission(
                    name=name,
                    resource=resource,
                    action=action,
                    description=description,
                ),
            )
