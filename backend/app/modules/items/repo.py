import uuid
from typing import Any

from sqlmodel import Session, col, func, select

from app.modules.items.models import Item


def get_by_id(
    *, session: Session, item_id: uuid.UUID, tenant_id: uuid.UUID | None
) -> Item | None:
    """Tenant filter lives in the WHERE clause: rows outside ``tenant_id``
    are invisible (natural 404). ``tenant_id=None`` = superuser bypass."""
    query = select(Item).where(Item.id == item_id)
    if tenant_id is not None:
        query = query.where(Item.tenant_id == tenant_id)
    return session.exec(query).first()


def get_multi(
    *,
    session: Session,
    tenant_id: uuid.UUID | None,
    owner_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[Item], int]:
    count_query = select(func.count()).select_from(Item)
    items_query = (
        select(Item).order_by(col(Item.created_at).desc()).offset(skip).limit(limit)
    )
    if tenant_id is not None:
        count_query = count_query.where(Item.tenant_id == tenant_id)
        items_query = items_query.where(Item.tenant_id == tenant_id)
    if owner_id is not None:
        count_query = count_query.where(Item.owner_id == owner_id)
        items_query = items_query.where(Item.owner_id == owner_id)
    count = session.exec(count_query).one()
    items = session.exec(items_query).all()
    return list(items), count


def create(*, session: Session, item: Item) -> Item:
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def update(*, session: Session, item: Item, update_data: dict[str, Any]) -> Item:
    item.sqlmodel_update(update_data)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def delete(*, session: Session, item: Item) -> None:
    session.delete(item)
    session.commit()
