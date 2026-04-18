import uuid
from typing import Any

from sqlmodel import Session, col, func, select

from app.modules.items.models import Item


def get_by_id(*, session: Session, item_id: uuid.UUID) -> Item | None:
    return session.get(Item, item_id)


def get_multi(
    *,
    session: Session,
    owner_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[Item], int]:
    count_query = select(func.count()).select_from(Item)
    items_query = (
        select(Item).order_by(col(Item.created_at).desc()).offset(skip).limit(limit)
    )
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
