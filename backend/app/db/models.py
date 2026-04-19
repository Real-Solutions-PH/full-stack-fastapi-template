"""Aggregator module so SQLModel.metadata sees every table.

Alembic autogenerate imports ``SQLModel`` from here; any new module-level
``table=True`` SQLModel must be re-exported below so its table is registered.
"""

from sqlmodel import SQLModel  # noqa: F401

from app.modules.iam.permissions.models import Permission  # noqa: F401
from app.modules.iam.roles.models import Role  # noqa: F401
from app.modules.iam.tenants.models import Tenant  # noqa: F401
from app.modules.iam.users.models import User  # noqa: F401
from app.modules.items.models import Item  # noqa: F401
from app.modules.ocr.models import OcrDocument  # noqa: F401
