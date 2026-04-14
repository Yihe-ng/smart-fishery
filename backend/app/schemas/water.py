from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel


class WaterQualityBase(BaseModel):
    pond_id: str
    dissolved_oxygen: float
    ph_value: float
    temperature: float
    ammonia_nitrogen: float
    nitrite: float


class WaterQualityCreate(WaterQualityBase):
    status: str = "正常"
    collect_time: datetime


class WaterQualityUpdate(BaseModel):
    dissolved_oxygen: Optional[float] = None
    ph_value: Optional[float] = None
    temperature: Optional[float] = None
    ammonia_nitrogen: Optional[float] = None
    nitrite: Optional[float] = None
    status: Optional[str] = None


class WaterQualityResponse(WaterQualityBase):
    id: int
    status: str
    collect_time: datetime

    class Config:
        from_attributes = True


class WaterQualityHistoryRequest(BaseModel):
    start_time: datetime
    end_time: datetime
    pond_id: Optional[str] = None


class WaterQualityHistoryResponse(BaseModel):
    data: List[WaterQualityResponse]
    total: int


class ThresholdRange(BaseModel):
    min: Optional[float] = None
    max: Optional[float] = None


class WaterQualityThresholdRule(BaseModel):
    label: str
    unit: str
    ideal: ThresholdRange
    warning: ThresholdRange
    critical: ThresholdRange


class DashboardFrameMetric(BaseModel):
    key: str
    label: str
    value: float
    unit: str
    statusText: Literal["正常", "警戒", "危险"]
    trendText: str
    isIdeal: bool


class DashboardFrameWaterQuality(BaseModel):
    id: str
    pondId: str
    temperature: float
    ph: float
    dissolvedOxygen: float
    ammoniaNitrogen: float
    nitrite: float
    collectTime: str
    status: str


class DashboardFrameDevice(BaseModel):
    id: str
    name: str
    type: str
    status: Literal["online", "offline", "error"]
    lastOnlineTime: Optional[str] = None
    lastData: Optional[float] = None
    unit: str
    location: str


class DashboardFrameAlert(BaseModel):
    id: str
    type: str
    level: Literal["critical", "warning", "info"]
    title: str
    message: str
    createTime: str
    status: Literal["pending", "resolved"]
    relatedDevice: Optional[str] = None


class DashboardFrameResponse(BaseModel):
    index: int
    nextIndex: int
    total: int
    hasNext: bool
    pondId: Optional[str] = None
    collectTime: Optional[str] = None
    waterQuality: Optional[DashboardFrameWaterQuality] = None
    previousWaterQuality: Optional[DashboardFrameWaterQuality] = None
    metrics: Dict[str, DashboardFrameMetric]
    devices: List[DashboardFrameDevice]
    alerts: List[DashboardFrameAlert]
