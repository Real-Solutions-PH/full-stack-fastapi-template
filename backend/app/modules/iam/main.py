from fastapi import APIRouter

from app.modules.iam.auth.main import router as auth_router
from app.modules.iam.permissions.main import router as permissions_router
from app.modules.iam.roles.main import router as roles_router
from app.modules.iam.tenants.main import router as tenants_router
from app.modules.iam.users.main import router as users_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(users_router)
router.include_router(roles_router)
router.include_router(permissions_router)
router.include_router(tenants_router)

__all__ = ["router"]
