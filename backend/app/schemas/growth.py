from pydantic import BaseModel, Field
from typing import List, Literal, Optional
import time


GrowthTaskStatus = Literal["success", "failed"]
GrowthStatus = Literal["small", "normal", "large"]
GrowthVideoTaskStatus = Literal["queued", "processing", "success", "failed"]


class GrowthImageMeta(BaseModel):
    src: str
    width: int
    height: int


class GrowthDetectionBBox(BaseModel):
    x: float
    y: float
    width: float
    height: float


class GrowthDetectionItem(BaseModel):
    id: str
    index: int
    status: GrowthStatus
    statusText: str
    confidence: float
    bbox: GrowthDetectionBBox
    bodyLengthCm: float
    weightG: float
    labelText: str


class GrowthStats(BaseModel):
    small: int = 0
    normal: int = 0
    large: int = 0
    detectedCount: int = 0


class GrowthSummary(BaseModel):
    avgBodyLengthCm: float = 0
    avgWeightG: float = 0


class GrowthDetectResponse(BaseModel):
    taskStatus: GrowthTaskStatus
    image: Optional[GrowthImageMeta] = None
    detections: List[GrowthDetectionItem] = Field(default_factory=list)
    selectedDetectionId: Optional[str] = None
    stats: GrowthStats = Field(default_factory=GrowthStats)
    summary: GrowthSummary = Field(default_factory=GrowthSummary)
    errorCode: Optional[str] = None


class GrowthVideoMeta(BaseModel):
    filename: str
    durationSec: float


class GrowthVideoFrameItem(BaseModel):
    frameId: str
    timestampSec: int
    image: GrowthImageMeta
    detections: List[GrowthDetectionItem] = Field(default_factory=list)
    selectedDetectionId: Optional[str] = None
    stats: GrowthStats = Field(default_factory=GrowthStats)
    summary: GrowthSummary = Field(default_factory=GrowthSummary)


class GrowthVideoDetectCreateResponse(BaseModel):
    taskId: str
    taskStatus: Literal["queued", "processing"]


class GrowthVideoDetectResultResponse(BaseModel):
    taskId: str
    taskStatus: GrowthVideoTaskStatus
    progress: int = 0
    video: Optional[GrowthVideoMeta] = None
    selectedFrameId: Optional[str] = None
    frames: List[GrowthVideoFrameItem] = Field(default_factory=list)
    aggregateStats: GrowthStats = Field(default_factory=GrowthStats)
    aggregateSummary: GrowthSummary = Field(default_factory=GrowthSummary)
    errorCode: Optional[str] = None
    startedAt: Optional[float] = None
