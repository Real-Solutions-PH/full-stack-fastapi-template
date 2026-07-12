"""Per-tenant rate-limit seam (#40).

A deliberately minimal choke point: every write route calls
:func:`check_rate_limit` with the request's :class:`TenantContext`. The
default :class:`NullBackend` always allows, so behavior is unchanged until a
real backend is swapped in at the module level.

# ponytail: NullBackend is the whole implementation on purpose. The upgrade
# path is a Redis token bucket (the compose stack already ships a redis
# service — do not add the dependency before it is needed) keyed on
# (tenant_id, key), which is also where the constitution §4 per-tenant AI
# spend caps plug in: meter cost per call, deny when the bucket or the
# tenant's spend budget is exhausted.
"""

import uuid
from typing import Protocol

from fastapi import HTTPException, status

from app.shared.tenancy import TenantContext


class RateLimitBackend(Protocol):
    """Decides whether a tenant may spend ``cost`` units against ``key``."""

    def allow(self, tenant_id: uuid.UUID, key: str, cost: int) -> bool: ...


class NullBackend:
    """Default backend: no limiting."""

    def allow(self, tenant_id: uuid.UUID, key: str, cost: int) -> bool:  # noqa: ARG002
        return True


backend: RateLimitBackend = NullBackend()


def check_rate_limit(tenant: TenantContext, key: str = "api", *, cost: int = 1) -> None:
    """Raise 429 (standard error envelope) when the tenant is over its limit."""
    if not backend.allow(tenant.tenant_id, key, cost):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded for tenant",
        )
