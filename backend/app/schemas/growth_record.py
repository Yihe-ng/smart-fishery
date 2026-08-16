from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from app.schemas.growth import GrowthCohortStatus

GrowthRecordSourceType = Literal["image", "video"]


class GrowthRecordCreate(BaseModel):
    """前端识别成功后上报的可测摘要（演示数据由前端跳过，不上报）。"""

    pondId: str = "T001"
    sourceType: GrowthRecordSourceType
    recognizedAt: datetime
    detectedCount: int = Field(default=0, ge=0)
    measurableCount: int = Field(default=0, ge=0)
    unmeasurableCount: int = Field(default=0, ge=0)
    small: int = Field(default=0, ge=0)
    normal: int = Field(default=0, ge=0)
    large: int = Field(default=0, ge=0)
    unassessed: int = Field(default=0, ge=0)
    plannedFrameCount: Optional[int] = Field(default=None, ge=0)
    completedFrameCount: Optional[int] = Field(default=None, ge=0)
    evaluableFrameCount: Optional[int] = Field(default=None, ge=0)
    detectionOccurrenceCount: Optional[int] = Field(default=None, ge=0)
    measurableOccurrenceCount: Optional[int] = Field(default=None, ge=0)
    cultureMonth: Optional[int] = None
    stockingAvgLengthCm: Optional[float] = None
    avgBodyLengthCm: float = 0
    avgWeightG: float = 0
    referenceLengthCm: Optional[float] = None
    smallThresholdCm: Optional[float] = None
    largeThresholdCm: Optional[float] = None
    trimmedMeanLengthCm: Optional[float] = None
    allMeasurableAvgLengthCm: Optional[float] = None
    cohortStatus: Optional[GrowthCohortStatus] = None
    advice: Optional[str] = None


class GrowthRecordResponse(BaseModel):
    id: int
    pondId: str
    sourceType: GrowthRecordSourceType
    recognizedAt: datetime
    measurableCount: int
    detectedCount: int
    unmeasurableCount: int
    small: int
    normal: int
    large: int
    unassessed: int
    plannedFrameCount: Optional[int] = None
    completedFrameCount: Optional[int] = None
    evaluableFrameCount: Optional[int] = None
    detectionOccurrenceCount: Optional[int] = None
    measurableOccurrenceCount: Optional[int] = None
    cultureMonth: Optional[int] = None
    stockingAvgLengthCm: Optional[float] = None
    avgBodyLengthCm: float
    avgWeightG: float
    referenceLengthCm: Optional[float] = None
    smallThresholdCm: Optional[float] = None
    largeThresholdCm: Optional[float] = None
    trimmedMeanLengthCm: Optional[float] = None
    allMeasurableAvgLengthCm: Optional[float] = None
    cohortStatus: Optional[GrowthCohortStatus] = None
    advice: Optional[str] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None


class GrowthRecordAssessmentUpdate(BaseModel):
    """轻量重评后仅更新月度评价相关字段，其余字段不可改。"""

    cultureMonth: Optional[int] = None
    stockingAvgLengthCm: Optional[float] = None
    referenceLengthCm: Optional[float] = None
    smallThresholdCm: Optional[float] = None
    largeThresholdCm: Optional[float] = None
    trimmedMeanLengthCm: Optional[float] = None
    allMeasurableAvgLengthCm: Optional[float] = None
    cohortStatus: Optional[GrowthCohortStatus] = None
    advice: Optional[str] = None


class GrowthRecordHistoryResponse(BaseModel):
    data: List[GrowthRecordResponse]
    total: int
