"""管线内部统一数据契约。

业务层（endpoint）只依赖本文件定义的数据类与协议，
不直接依赖 Ultralytics Results / torchvision logits / YOLO class index。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional, Protocol, Tuple

import numpy as np


# ---------------------------------------------------------------------------
# 统一语义常量（与训练端合同一致）
# ---------------------------------------------------------------------------

# class 0 = fish_measurable，class 1 = fish_unmeasurable（训练端 CLASS_NAMES 合同）
CLASS_NAME_MEASURABLE = "fish_measurable"
CLASS_NAME_UNMEASURABLE = "fish_unmeasurable"


# ---------------------------------------------------------------------------
# 分割输出
# ---------------------------------------------------------------------------


@dataclass
class FishInstance:
    """单条鱼的标准化分割结果（像素坐标、全分辨率 mask）。"""

    instance_id: str
    bbox_xyxy: Tuple[float, float, float, float]  # (x0, y0, x1, y1) 像素，x1/y1 为 exclusive
    mask: np.ndarray  # 全分辨率 bool 数组 (H, W)
    segmentation_confidence: float  # [0, 1]
    source_shape: Tuple[int, int]  # (width, height)
    class_name: Optional[str] = None  # 分割器原生类别名（可空，业务层不依赖）
    metadata: dict[str, Any] = field(default_factory=dict)


class FishSegmenterProtocol(Protocol):
    """统一分割抽象：输入 RGB 图像，输出标准化实例列表。"""

    def predict(self, image_rgb: np.ndarray) -> List[FishInstance]: ...


# ---------------------------------------------------------------------------
# Crop 输出
# ---------------------------------------------------------------------------


@dataclass
class Crop:
    """单条鱼的分类输入 crop（RGB，uint8，224×224 由 manifest 决定）。"""

    instance_id: str
    image_rgb: np.ndarray  # (input_size, input_size, 3) uint8 RGB
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# 可测性分类器
# ---------------------------------------------------------------------------


class MeasurabilityClassifierProtocol(Protocol):
    """统一可测性分类器抽象。

    业务层只认 P(measurable) ∈ [0,1]，不认具体 backbone 的 class index / logits。
    """

    def predict_proba(
        self,
        crops: List[Crop],
        *,
        batch_size: Optional[int] = None,
    ) -> List[float]: ...


# ---------------------------------------------------------------------------
# 时序策略
# ---------------------------------------------------------------------------


@dataclass
class TemporalOutcome:
    """时序平滑后的单条鱼概率结果。"""

    instance_id: str
    single_probability: float  # 当前帧单帧 P(measurable)
    final_probability: float  # 时序后 P(measurable)
    applied: bool  # 是否实际使用了历史帧
    policy: str  # 实际使用的策略名
    fallback_reason: Optional[str] = None  # 未使用时序的原因（fallback 合同）
    history_count: int = 0  # 使用的历史帧数（0/1/2）


class TemporalPolicyProtocol(Protocol):
    """可插拔时序策略抽象。

    状态必须按 stream_id 隔离；支持 reset / clear_expired（TTL）。
    统一 fallback：历史缺失/被拒/歧义 -> 当前单帧概率，绝不丢鱼。
    """

    name: str

    def reset(self, stream_id: str) -> None: ...

    def clear_expired(self, now: Optional[float] = None) -> int: ...

    def apply(
        self,
        stream_id: str,
        frame_meta: dict[str, Any],
        instances: List[FishInstance],
        probabilities: List[float],
    ) -> List[TemporalOutcome]: ...

    def update(
        self,
        stream_id: str,
        frame_meta: dict[str, Any],
        instances: List[FishInstance],
        probabilities: List[float],
    ) -> None: ...


# ---------------------------------------------------------------------------
# 管线最终输出
# ---------------------------------------------------------------------------


@dataclass
class PipelineFish:
    """管线内部统一的“每条鱼”结果（API 层再做兼容映射）。"""

    instance_id: str
    bbox_xyxy: Tuple[float, float, float, float]
    mask: np.ndarray  # 全分辨率 bool (H, W)
    polygon_px: np.ndarray  # 像素多边形 (N, 2)
    polygon_norm: List[List[float]]  # 归一化多边形（前端 SVG 使用）
    segmentation_confidence: float
    single_measurable_probability: float
    final_measurable_probability: float
    is_measurable: bool
    temporal_applied: bool
    temporal_policy: str
    temporal_fallback_reason: Optional[str] = None
    temporal_history_count: int = 0
    measurement_method: Optional[str] = None
    measurement_confidence: Optional[float] = None
    measurement_reasons: Optional[List[str]] = None
    visible_mask_length_px: Optional[float] = None
    primary_length_px: Optional[float] = None
    measurement_debug: dict[str, Any] = field(default_factory=dict)
    # 影子策略结果（geometry_rescue 候选，仅计算；legacy API 映射不输出此字段）
    rescue_shadow: Optional[dict[str, Any]] = None

    @property
    def class_name(self) -> str:
        """统一类别绑定：P(measurable) 阈值决策 -> 语义类别名。"""
        return (
            CLASS_NAME_MEASURABLE
            if self.is_measurable
            else CLASS_NAME_UNMEASURABLE
        )


@dataclass
class FrameAnalysisOutput:
    """单帧管线输出。"""

    width: int
    height: int
    fish: List[PipelineFish] = field(default_factory=list)
    debug: Optional[dict[str, Any]] = None
