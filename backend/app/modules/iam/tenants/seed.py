from sqlmodel import Session

from app.modules.iam.tenants import repo as tenant_repo
from app.modules.iam.tenants.models import Tenant

DEFAULT_TENANTS: list[dict[str, str]] = [
    {"name": "Default", "slug": "default"},
]


def seed_tenants(session: Session) -> None:
    for entry in DEFAULT_TENANTS:
        if tenant_repo.get_by_slug(session=session, slug=entry["slug"]) is None:
            tenant_repo.create(session=session, tenant=Tenant(**entry))
