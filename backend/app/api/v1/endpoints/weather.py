"""天气API端点 - 提供实时天气和气压风险等级"""

from fastapi import APIRouter, Query
from typing import Optional

from app.schemas.base import BaseResponse
from app.services.weather_service import weather_service

router = APIRouter()


@router.get("/current", response_model=BaseResponse[dict])
async def get_current_weather(
    latitude: float = Query(21.75, description="纬度"),
    longitude: float = Query(111.75, description="经度"),
    force_refresh: bool = Query(False, description="强制刷新缓存")
):
    """
    获取当前天气数据

    包含：
    - 当前温度、气压、风速、湿度
    - 气压风险等级（高/中/低）
    - 投喂建议
    """
    weather_data = await weather_service.get_current_weather(
        latitude=latitude,
        longitude=longitude,
        force_refresh=force_refresh
    )

    return BaseResponse[dict](
        code=200,
        msg="获取天气成功",
        data=weather_data
    )
