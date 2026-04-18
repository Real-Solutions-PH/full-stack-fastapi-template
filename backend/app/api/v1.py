from fastapi import APIRouter

from app.modules.iam.main import router as iam_router
from app.modules.items.main import router as items_router
from app.modules.system.main import router as system_router

v1_router = APIRouter()
v1_router.include_router(iam_router)
v1_router.include_router(items_router)
v1_router.include_router(system_router)
