from fastapi import APIRouter
from app.api.v1.endpoints import auth, water_quality, user, role, menu, fish_pond, feeding, device, alert, health, disease, growth

api_router = APIRouter()

# 包含认证路由
api_router.include_router(auth.router, tags=["认证"])

# 包含水质检测路由
api_router.include_router(water_quality.router, prefix="/water-quality", tags=["水质检测"])

# 包含用户管理路由
api_router.include_router(user.router, prefix="/user", tags=["用户管理"])

# 包含角色管理路由
api_router.include_router(role.router, prefix="/role", tags=["角色管理"])

# 包含菜单管理路由
api_router.include_router(menu.router, prefix="/v3/system/menus", tags=["菜单管理"])

# 包含鱼塘管理路由
api_router.include_router(fish_pond.router, prefix="/fish-pond", tags=["鱼塘管理"])

# 包含投喂管理路由
api_router.include_router(feeding.router, prefix="/feeding", tags=["投喂管理"])

# 包含设备管理路由
api_router.include_router(device.router, prefix="/device", tags=["设备管理"])

# 包含告警管理路由
api_router.include_router(alert.router, prefix="/alert", tags=["告警管理"])

# 包含健康总览路由
api_router.include_router(health.router, prefix="/health", tags=["健康总览"])

# 包含病害检测路由
api_router.include_router(disease.router, prefix="/disease", tags=["病害检测"])

# 包含生长趋势分析路由
api_router.include_router(growth.router, prefix="/growth", tags=["生长趋势分析"])
