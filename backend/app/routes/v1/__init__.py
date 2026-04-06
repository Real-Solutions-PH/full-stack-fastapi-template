from fastapi import APIRouter

from app.core.config import settings
from app.routes.v1 import items, login, users, utils

v1_router = APIRouter()
v1_router.include_router(login.router)
v1_router.include_router(users.router)
v1_router.include_router(utils.router)
v1_router.include_router(items.router)

if settings.ENVIRONMENT == "local":
    from app.routes.v1 import private

    v1_router.include_router(private.router)
