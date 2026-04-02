from fastapi import APIRouter

from app.agent.router import router as ai_router
from app.api.v1.endpoints import (
    alert,
    auth,
    device,
    feeding,
    fish_pond,
    growth,
    health,
    menu,
    role,
    user,
    water_quality,
    weather,
)

api_router = APIRouter()

api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(
    water_quality.router, prefix="/water-quality", tags=["water-quality"]
)
api_router.include_router(user.router, prefix="/user", tags=["user"])
api_router.include_router(role.router, prefix="/role", tags=["role"])
api_router.include_router(menu.router, prefix="/v3/system/menus", tags=["menu"])
api_router.include_router(fish_pond.router, prefix="/fish-pond", tags=["fish-pond"])
api_router.include_router(feeding.router, prefix="/feeding", tags=["feeding"])
api_router.include_router(device.router, prefix="/device", tags=["device"])
api_router.include_router(alert.router, prefix="/alert", tags=["alert"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(growth.router, prefix="/growth", tags=["growth"])
api_router.include_router(weather.router, prefix="/weather", tags=["weather"])
api_router.include_router(ai_router, prefix="/agent", tags=["ai-gateway"])
