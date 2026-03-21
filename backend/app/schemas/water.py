from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class WaterQualityBase(BaseModel):
    """水质数据基础模型"""

    pond_id: str
    dissolved_oxygen: float
    ph_value: float
    temperature: float
    ammonia_nitrogen: float
    nitrite: float


class WaterQualityCreate(WaterQualityBase):
    """创建水质数据模型"""

    status: str = "正常"
    collect_time: datetime


class WaterQualityUpdate(BaseModel):
    """更新水质数据模型"""

    dissolved_oxygen: Optional[float] = None
    ph_value: Optional[float] = None
    temperature: Optional[float] = None
    ammonia_nitrogen: Optional[float] = None
    nitrite: Optional[float] = None
    status: Optional[str] = None


class WaterQualityResponse(WaterQualityBase):
    """水质数据响应模型"""

    id: int
    status: str
    collect_time: datetime

    class Config:
        from_attributes = True


class WaterQualityHistoryRequest(BaseModel):
    """历史数据查询请求"""

    start_time: datetime
    end_time: datetime
    pond_id: Optional[str] = None


class WaterQualityHistoryResponse(BaseModel):
    """历史数据响应"""

    data: List[WaterQualityResponse]
    total: int
