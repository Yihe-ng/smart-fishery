from fastapi import APIRouter
from app.api.v1.endpoints import auth, water_quality, user, role, menu

api_router = APIRouter()

# 包含认证路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])

# 包含水质检测路由
api_router.include_router(water_quality.router, prefix="/water-quality", tags=["水质检测"])

# 包含用户管理路由
api_router.include_router(user.router, prefix="/user", tags=["用户管理"])

# 包含角色管理路由
api_router.include_router(role.router, prefix="/role", tags=["角色管理"])

# 包含菜单管理路由
api_router.include_router(menu.router, prefix="/v3/system/menus", tags=["菜单管理"])
