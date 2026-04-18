import uuid
from typing import Any

from fastapi import APIRouter

from app.modules.iam.deps import CurrentUser
from app.modules.items import services as item_service
from app.modules.items.schema import ItemCreate, ItemPublic, ItemsPublic, ItemUpdate
from app.shared.deps import SessionDep
from app.shared.schema import Message

router = APIRouter(prefix="/items", tags=["items"])


@router.get("/", response_model=ItemsPublic)
def read_items(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    items, count = item_service.list_items(
        session=session, current_user=current_user, skip=skip, limit=limit
    )
    items_public = [ItemPublic.model_validate(item) for item in items]
    return ItemsPublic(data=items_public, count=count)


@router.get("/{id}", response_model=ItemPublic)
def read_item(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    return item_service.get_item(
        session=session, current_user=current_user, item_id=id
    )


@router.post("/", response_model=ItemPublic)
def create_item(
    *, session: SessionDep, current_user: CurrentUser, item_in: ItemCreate
) -> Any:
    return item_service.create_item(
        session=session, current_user=current_user, item_in=item_in
    )


@router.put("/{id}", response_model=ItemPublic)
def update_item(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    item_in: ItemUpdate,
) -> Any:
    return item_service.update_item(
        session=session, current_user=current_user, item_id=id, item_in=item_in
    )


@router.delete("/{id}")
def delete_item(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    item_service.delete_item(
        session=session, current_user=current_user, item_id=id
    )
    return Message(message="Item deleted successfully")
