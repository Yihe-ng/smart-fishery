"""天气服务模块 - 集成 Open-Meteo API 并提供渔业气压风险等级"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import httpx


class WeatherService:
    """天气服务 - 获取实时天气并计算渔业风险等级"""

    # 缓存配置
    CACHE_DURATION = 300  # 5分钟缓存

    # 气压风险等级阈值 (hPa)
    PRESSURE_THRESHOLDS = {
        "high": 1010,  # > 1010 低风险
        "medium": 1000,  # 1000-1010 中风险
        # < 1000 高风险
    }

    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._cache_time: Optional[float] = None
        self._lock = asyncio.Lock()

    def _calculate_pressure_risk(self, pressure: float) -> Dict[str, Any]:
        """
        计算气压风险等级

        渔业气压风险标准：
        - 高风险: < 1000 hPa - 鱼类应激，建议减少投喂或停喂
        - 中风险: 1000-1010 hPa - 适当减少投喂量
        - 低风险: > 1010 hPa - 正常投喂
        """
        if pressure < self.PRESSURE_THRESHOLDS["medium"]:
            level = "high"
            text = "高风险"
            description = "气压偏低，鱼类可能产生应激反应，建议减少投喂量或暂停投喂"
            feeding_suggestion = "建议减少30%-50%投喂量"
        elif pressure < self.PRESSURE_THRESHOLDS["high"]:
            level = "medium"
            text = "中风险"
            description = "气压略低，建议适当减少投喂量并密切观察鱼类状态"
            feeding_suggestion = "建议减少10%-20%投喂量"
        else:
            level = "low"
            text = "低风险"
            description = "气压正常，适合正常投喂"
            feeding_suggestion = "可按正常计划投喂"

        return {
            "level": level,
            "text": text,
            "description": description,
            "feedingSuggestion": feeding_suggestion,
            "pressure": pressure,
        }

    async def _fetch_from_open_meteo(
        self, latitude: float = 21.75, longitude: float = 111.75
    ) -> Dict[str, Any]:
        """从 Open-Meteo 获取天气数据"""
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,surface_pressure,wind_speed_10m,weather_code",
            "timezone": "Asia/Shanghai",
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    def _transform_weather_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """转换并增强天气数据"""
        current = raw_data.get("current", {})

        pressure = current.get("surface_pressure", 1013)
        risk_info = self._calculate_pressure_risk(pressure)

        return {
            "current": {
                "temperature": round(current.get("temperature_2m", 0)),
                "pressure": round(pressure),
                "windSpeed": round(current.get("wind_speed_10m", 0), 1),
                "humidity": current.get("relative_humidity_2m", 0),
                "weatherCode": current.get("weather_code", 0),
            },
            "pressureRisk": risk_info,
            "location": "广东阳西",
            "updateTime": datetime.now().strftime("%H:%M"),
        }

    async def get_current_weather(
        self, latitude: float = 21.75, longitude: float = 111.75, force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        获取当前天气（带缓存）

        Args:
            latitude: 纬度
            longitude: 经度
            force_refresh: 强制刷新缓存

        Returns:
            天气数据包含气压风险等级
        """
        cache_key = f"{latitude},{longitude}"

        async with self._lock:
            # 检查缓存是否有效
            if not force_refresh and self._cache_time:
                elapsed = time.time() - self._cache_time
                if elapsed < self.CACHE_DURATION and cache_key in self._cache:
                    return self._cache[cache_key]

            # 获取新数据
            raw_data = await self._fetch_from_open_meteo(latitude, longitude)
            weather_data = self._transform_weather_data(raw_data)

            # 更新缓存
            self._cache[cache_key] = weather_data
            self._cache_time = time.time()

            return weather_data

    def get_pressure_risk_for_feeding(self, pressure: Optional[float] = None) -> Dict[str, Any]:
        """
        获取气压风险信息（用于投喂建议）

        Args:
            pressure: 气压值，如果不提供则返回默认低风险

        Returns:
            风险等级信息
        """
        if pressure is None:
            pressure = 1013  # 默认标准气压
        return self._calculate_pressure_risk(pressure)

    async def clear_cache(self):
        """清除缓存"""
        async with self._lock:
            self._cache.clear()
            self._cache_time = None


# 全局服务实例
weather_service = WeatherService()
