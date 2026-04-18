import uuid
from typing import Any

from fastapi import APIRouter, Depends

from app.modules.iam.deps import get_current_active_superuser
from app.modules.iam.tenants import services as tenant_service
from app.modules.iam.tenants.schema import TenantPublic, TenantsPublic
from app.shared.deps import SessionDep

router = APIRouter(
    prefix="/tenants",
    tags=["tenants"],
    dependencies=[Depends(get_current_active_superuser)],
)


@router.get("/", response_model=TenantsPublic)
def read_tenants(session: SessionDep, skip: int = 0, limit: int = 100) -> Any:
    tenants, count = tenant_service.list_tenants(
        session=session, skip=skip, limit=limit
    )
    return TenantsPublic(
        data=[TenantPublic.model_validate(t) for t in tenants], count=count
    )


@router.get("/{tenant_id}", response_model=TenantPublic)
def read_tenant(session: SessionDep, tenant_id: uuid.UUID) -> Any:
    return tenant_service.get_tenant(session=session, tenant_id=tenant_id)
