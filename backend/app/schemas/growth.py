from pydantic import BaseModel, Field
from typing import List, Literal, Optional
import time


GrowthTaskStatus = Literal["success", "failed"]
# 单鱼生长状态：small/normal/large 已完成月度分档；unassessed 表示"能测但未评"
# （缺养殖月数或评价配置不可用）；unmeasurable 表示"测不了"，不参与任何平均值。
GrowthStatus = Literal["small", "normal", "large", "unassessed", "unmeasurable"]
# 群体状态：insufficient=有效可测样本不足；unassessed=未提供养殖参数，仅完成测量。
GrowthCohortStatus = Literal["small", "normal", "large", "insufficient", "unassessed"]
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
    maskPolygons: List[List[float]] = Field(default_factory=list)
    # New measurement metadata fields (backward-compatible — all optional)
    measurementMethod: Optional[str] = None
    measurementConfidence: Optional[float] = None
    visibleMaskLengthCm: Optional[float] = None
    measurementReasons: Optional[List[str]] = None
    className: Optional[str] = None
    isMeasurable: bool = True
    measurabilityLabel: str = "可测"
    # ---- 可选 debug 字段（仅 two_stage 管线填充；legacy 为 None）----
    instanceId: Optional[str] = None
    segmentationConfidence: Optional[float] = None
    singleMeasurableProbability: Optional[float] = None
    finalMeasurableProbability: Optional[float] = None
    temporalApplied: Optional[bool] = None
    temporalPolicy: Optional[str] = None
    temporalFallbackReason: Optional[str] = None
    temporalHistoryCount: Optional[int] = None


class GrowthStats(BaseModel):
    small: int = 0
    normal: int = 0
    large: int = 0
    # 可测但未做月度评价的数量（缺养殖参数或评价配置不可用）
    unassessed: int = 0
    detectedCount: int = 0
    measurableCount: int = 0
    unmeasurableCount: int = 0


class GrowthSummary(BaseModel):
    avgBodyLengthCm: float = 0
    avgWeightG: float = 0


class GrowthAssessment(BaseModel):
    """月度生长评价结论（由后端养殖标准服务生成，前端只负责格式化展示）。

    长度字段单位均为 cm，已按展示口径保留一位小数；后端判断使用未四舍五入原始值。
    月份或投苗体长缺失时不产出本模型（响应中 assessment 为 null）。
    """

    # 养殖月数（从投苗日起，3–15）
    cultureMonth: Optional[int] = None
    # 投苗时平均全长
    stockingAvgLengthCm: Optional[float] = None
    # 当月综合参考全长 = 投苗体长 + 该月预期累计增长量
    referenceLengthCm: Optional[float] = None
    # 偏小下限 / 偏大上限（综合参考全长 × 可配置比例，默认 ±15% 工程容差）
    smallThresholdCm: Optional[float] = None
    largeThresholdCm: Optional[float] = None
    # 群体评价平均全长（已去掉一条最短记录）
    trimmedMeanLengthCm: Optional[float] = None
    # 全部可测鱼平均全长（不去极端值）
    allMeasurableAvgLengthCm: Optional[float] = None
    cohortStatus: GrowthCohortStatus = "unassessed"
    # 有效可测样本是否达到群体评价最小数量
    sampleSufficient: bool = False
    # 确定性规则生成的管理建议，不含具体投喂克数
    advice: str = ""


class GrowthDetectResponse(BaseModel):
    taskStatus: GrowthTaskStatus
    image: Optional[GrowthImageMeta] = None
    detections: List[GrowthDetectionItem] = Field(default_factory=list)
    selectedDetectionId: Optional[str] = None
    stats: GrowthStats = Field(default_factory=GrowthStats)
    summary: GrowthSummary = Field(default_factory=GrowthSummary)
    errorCode: Optional[str] = None
    # 评价失败或未提供养殖参数时为 None，此时测量结果仍然有效
    assessment: Optional[GrowthAssessment] = None


class FishMeasurementInput(BaseModel):
    """轻量重评的单鱼测量输入：只带标识、可测性与体长，不含图片与掩码。"""

    id: str
    isMeasurable: bool = True
    bodyLengthCm: float = 0.0


class GrowthEvaluateRequest(BaseModel):
    """轻量重评请求：修改养殖参数后重算业务状态，不重新上传图片、不跑模型。"""

    cultureMonth: Optional[int] = None
    stockingAvgLengthCm: Optional[float] = None
    fishMeasurements: List[FishMeasurementInput] = Field(default_factory=list)


class GrowthEvaluatedFishItem(BaseModel):
    """重评后的单鱼状态，供前端合并覆盖当前检测项的 status / statusText。"""

    id: str
    status: GrowthStatus
    statusText: str


class GrowthEvaluateResponse(BaseModel):
    detections: List[GrowthEvaluatedFishItem] = Field(default_factory=list)
    stats: GrowthStats = Field(default_factory=GrowthStats)
    summary: GrowthSummary = Field(default_factory=GrowthSummary)
    assessment: Optional[GrowthAssessment] = None
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
