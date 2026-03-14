from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class WaterQualityBase(BaseModel):
    """水质数据基础模型"""
    dissolved_oxygen: float  # 溶解氧 mg/L
    ph_value: float          # pH值
    temperature: float       # 温度 ℃
    ammonia_nitrogen: float  # 氨氮 mg/L
    nitrite: float           # 亚硝酸盐 mg/L
    sensor_id: str
    pond_id: str


class WaterQualityCreate(WaterQualityBase):
    """创建水质数据模型"""
    pass


class WaterQualityUpdate(BaseModel):
    """更新水质数据模型"""
    dissolved_oxygen: Optional[float] = None
    ph_value: Optional[float] = None
    temperature: Optional[float] = None
    ammonia_nitrogen: Optional[float] = None
    nitrite: Optional[float] = None


class WaterQualityResponse(WaterQualityBase):
    """水质数据响应模型"""
    id: int
    created_at: datetime
    analysis_result: Optional[str] = None
    alert_level: Optional[str] = None

    class Config:
        from_attributes = True


class WaterQualityHistoryRequest(BaseModel):
    """历史数据查询请求"""
    start_time: datetime
    end_time: datetime
    sensor_id: Optional[str] = None
    pond_id: Optional[str] = None


class WaterQualityHistoryResponse(BaseModel):
    """历史数据响应"""
    data: List[WaterQualityResponse]
    total: int


class SensorDeviceBase(BaseModel):
    """传感器设备基础模型"""
    device_id: str
    device_name: str
    pond_id: str
    status: str


class SensorDeviceCreate(SensorDeviceBase):
    """创建传感器设备模型"""
    pass


class SensorDeviceResponse(SensorDeviceBase):
    """传感器设备响应模型"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
