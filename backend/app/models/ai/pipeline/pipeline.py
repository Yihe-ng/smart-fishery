"""FishAnalysisPipeline：统一两阶段推理编排。

结构：
    FishSegmenter -> CropBuilder -> MeasurabilityClassifier(batch)
    -> TemporalProcessor(可插拔) -> threshold -> FishLengthMeasurement

endpoint 不知道具体 YOLO/ResNet/MobileNet 实现、crop 公式、时序公式、
classifier logits；这些都封装在 pipeline 与 manifest 内。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import cv2
import numpy as np

from app.models.ai.pipeline.admission_policy import (
    AdmissionPolicyConfig,
    MASK_ABNORMAL_CODES,
    evaluate_admission,
)
from app.models.ai.pipeline.classifier_adapters import MeasurabilityClassifierProtocol
from app.services.fish_length_measurement import measure_fish_length
from app.models.ai.pipeline.contracts import (
    CLASS_NAME_MEASURABLE,
    CLASS_NAME_UNMEASURABLE,
    FishInstance,
    FishSegmenterProtocol,
    FrameAnalysisOutput,
    PipelineFish,
    TemporalPolicyProtocol,
)
from app.models.ai.pipeline.crop_builder import CropBuilder
from app.models.ai.pipeline.manifest import ModelManifest
from app.models.ai.pipeline.model_manager import ModelManager
from app.models.ai.pipeline.temporal import (
    create_temporal_policy,
)


# 复刻 legacy YOLODetector 的 mask 多边形提取参数
MASK_CONTOUR_APPROX_RATIO = 0.002
MASK_CONTOUR_MIN_EPSILON_PX = 1.0


def extract_mask_polygons(
    mask: np.ndarray,
    image_width: int,
    image_height: int,
) -> tuple[Optional[np.ndarray], Optional[List[List[float]]]]:
    """从 bool mask 提取最大外部轮廓 -> (像素多边形, 归一化多边形)。"""
    if image_width <= 0 or image_height <= 0:
        return None, None
    binary = (mask.astype(np.uint8)) * 255
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None, None
    largest = max(contours, key=cv2.contourArea)
    if cv2.contourArea(largest) <= 0:
        return None, None
    perimeter = cv2.arcLength(largest, True)
    epsilon = max(MASK_CONTOUR_MIN_EPSILON_PX, perimeter * MASK_CONTOUR_APPROX_RATIO)
    approx = cv2.approxPolyDP(largest, epsilon, True).reshape(-1, 2).astype(np.float32)
    if len(approx) < 3:
        return None, None
    normalized = [
        [
            float(np.clip(x / image_width, 0.0, 1.0)),
            float(np.clip(y / image_height, 0.0, 1.0)),
        ]
        for x, y in approx
    ]
    return approx, normalized


class FishAnalysisPipeline:
    """统一两阶段推理管线（图片/视频共用，时序策略由 manifest 决定）。"""

    def __init__(
        self,
        *,
        segmenter: FishSegmenterProtocol,
        crop_builder: CropBuilder,
        classifier: MeasurabilityClassifierProtocol,
        temporal_policy: TemporalPolicyProtocol,
        manifest: ModelManifest,
        max_instances: Optional[int] = None,
    ):
        self._segmenter = segmenter
        self._crop_builder = crop_builder
        self._classifier = classifier
        self._temporal_policy = temporal_policy
        self._manifest = manifest
        if max_instances is not None and max_instances < 1:
            raise ValueError("max_instances 必须 >= 1")
        self._max_instances = max_instances

    @classmethod
    def from_manifest(
        cls,
        manifest: ModelManifest,
        *,
        device: str = "cpu",
        temporal_ttl_seconds: float = 60 * 60,
        max_instances: Optional[int] = None,
    ) -> "FishAnalysisPipeline":
        """由 manifest 构建完整管线（ModelManager 统一模型生命周期）。"""
        manager = ModelManager(manifest, device=device)
        crop = manifest.crop
        crop_builder = CropBuilder(
            margin_fraction_each_side=crop.margin_fraction_each_side,
            bbox_scale=crop.bbox_scale,
            tile_size=crop.tile_size,
            padding_value=crop.padding_value,
            mask_focus_outside_brightness=crop.mask_focus_outside_brightness,
        )
        temporal_cfg = manifest.temporal
        temporal_policy = create_temporal_policy(
            temporal_cfg.policy,
            window=temporal_cfg.window,
            max_frame_gap=temporal_cfg.max_frame_gap,
            ttl_seconds=temporal_ttl_seconds,
        )
        return cls(
            segmenter=manager.segmenter,
            crop_builder=crop_builder,
            classifier=manager.classifier,
            temporal_policy=temporal_policy,
            manifest=manifest,
            max_instances=max_instances,
        )

    @property
    def manifest(self) -> ModelManifest:
        return self._manifest

    def analyze_image(
        self,
        image_rgb: np.ndarray,
        image_meta: Optional[Dict[str, Any]] = None,
    ) -> FrameAnalysisOutput:
        """图片模式：时序永远 disabled。"""
        meta = dict(image_meta or {})
        return self._analyze(
            image_rgb,
            meta,
            stream_id=None,
            temporal_enabled=False,
        )

    def analyze_frame(
        self,
        image_rgb: np.ndarray,
        image_meta: Optional[Dict[str, Any]] = None,
        *,
        stream_id: str,
        frame_index: int,
        timestamp_sec: Optional[float] = None,
        temporal_enabled_override: Optional[bool] = None,
    ) -> FrameAnalysisOutput:
        """视频/流模式：时序由 manifest 或 override 决定（默认 disabled）。"""
        meta = dict(image_meta or {})
        meta["stream_id"] = stream_id
        meta["frame_index"] = frame_index
        meta["timestamp_sec"] = timestamp_sec
        temporal_enabled = (
            temporal_enabled_override
            if temporal_enabled_override is not None
            else self._manifest.temporal.enabled_for_video
        )
        return self._analyze(
            image_rgb,
            meta,
            stream_id=stream_id,
            temporal_enabled=temporal_enabled,
        )

    def reset_temporal_state(self, stream_id: str) -> None:
        """显式重置某路 stream 的时序状态（新视频任务开始前调用）。"""
        self._temporal_policy.reset(stream_id)

    def clear_expired_temporal_state(self) -> int:
        """TTL 清理（防止内存泄漏/跨任务污染）。"""
        return self._temporal_policy.clear_expired()

    # ------------------------------------------------------------------
    # 内部实现
    # ------------------------------------------------------------------

    def _analyze(
        self,
        image_rgb: np.ndarray,
        image_meta: Dict[str, Any],
        *,
        stream_id: Optional[str],
        temporal_enabled: bool,
    ) -> FrameAnalysisOutput:
        height, width = image_rgb.shape[:2]
        if height <= 0 or width <= 0:
            raise ValueError("INVALID_IMAGE")

        # 1) 分割
        instances = self._segmenter.predict(image_rgb)
        if self._max_instances is not None:
            instances = instances[: self._max_instances]
        if not instances:
            return FrameAnalysisOutput(width=width, height=height, fish=[])

        # 2) crop（顺序与 instances 对齐）
        crops = self._crop_builder.build_many(image_rgb, instances)

        # 3) 分类 batch（顺序与 instance_id 对齐）
        probabilities = self._classifier.predict_proba(
            crops, batch_size=self._manifest.classifier.batch_size
        )
        if len(probabilities) != len(instances):
            raise RuntimeError("分类器输出数量与实例数量不一致")

        # 4) 时序（图片模式强制 disabled；视频由 manifest/override 决定）
        frame_meta: Dict[str, Any] = {
            "frame_index": int(image_meta.get("frame_index", 0)),
            "timestamp_sec": image_meta.get("timestamp_sec"),
            "image_diag": float(np.hypot(width, height)),
        }
        if temporal_enabled and stream_id is not None:
            outcomes = self._temporal_policy.apply(
                stream_id, frame_meta, instances, probabilities
            )
            self._temporal_policy.update(
                stream_id, frame_meta, instances, probabilities
            )
        else:
            outcomes = [
                self._disabled_outcome(instance, probability)
                for instance, probability in zip(instances, probabilities)
            ]

        # 5) 分割置信度、分类阈值和几何质量融合：三道门槛共同决定是否可测。
        threshold = self._manifest.classifier.threshold
        min_segmentation_confidence = (
            self._manifest.segmentation.min_confidence_for_measurement
        )
        fish: List[PipelineFish] = []
        for instance, outcome, probability in zip(instances, outcomes, probabilities):
            classifier_is_measurable = outcome.final_probability >= threshold
            segmentation_is_sufficient = (
                instance.segmentation_confidence >= min_segmentation_confidence
            )
            polygon_px, polygon_norm = extract_mask_polygons(
                instance.mask, width, height
            )
            measurement_method: Optional[str] = None
            measurement_confidence: Optional[float] = None
            measurement_reasons: Optional[List[str]] = None
            visible_mask_length_px: Optional[float] = None
            primary_length_px: Optional[float] = None
            measurement_debug: Dict[str, Any] = {}

            if polygon_px is not None:
                try:
                    measurement = measure_fish_length(
                        polygon_px,
                        width,
                        height,
                        mask=instance.mask,
                        rgb_image=image_rgb,
                        config=self._manifest.measurement,
                    )
                    if measurement.primary_length_px > 0:
                        primary_length_px = measurement.primary_length_px
                    measurement_method = measurement.measurement_method
                    measurement_reasons = measurement.reasons or None
                    visible_mask_length_px = measurement.visible_mask_length_px
                    measurement_confidence = measurement.geometry_confidence
                    measurement_debug = {
                        "geometry_is_measurable": measurement.is_measurable,
                        "secondary_component_ratio": measurement.secondary_component_ratio,
                        "hole_count": measurement.hole_count,
                        "hole_area_ratio": measurement.hole_area_ratio,
                        "highlight_ratio": measurement.highlight_ratio,
                        "core_area_ratio": measurement.core_area_ratio,
                        "core_component_count": measurement.core_component_count,
                        "axis_stability": measurement.axis_stability,
                        "path_score": measurement.path_score,
                        "path_score_gap": measurement.path_score_gap,
                        "path_turn_rate": measurement.path_turn_rate,
                        "curvature_ratio": measurement.curvature_ratio,
                        "straightness_ratio": measurement.straightness_ratio,
                        "main_axis_length_px": measurement.main_axis_length_px,
                        "centerline_length_px": measurement.centerline_length_px,
                        "adhesion_suspected": measurement.adhesion_suspected,
                        "path_ambiguous": measurement.path_ambiguous,
                        "path_points": measurement.path_points,
                        "quality_features": measurement.quality_features,
                    }
                except Exception as exc:
                    measurement_method = "none"
                    measurement_reasons = ["measurement_exception", type(exc).__name__]
                    measurement_confidence = 0.0

            # 5) 准入策略：统一入口（strict 正式行为 + geometry_rescue 影子）
            #    strict 模式与历史行为逐字段一致；影子模式仅计算不改变 API 输出。
            measurement_reasons_original = list(measurement_reasons or [])
            component_audit = instance.metadata.get("cleaned_component_audit") or {}
            mask_abnormal = bool(
                set(measurement_reasons_original) & MASK_ABNORMAL_CODES
            ) or bool(
                component_audit.get("multi_component_review")
                and component_audit.get("removed_component_count", 0) > 0
            )
            evaluation = evaluate_admission(
                classifier_is_measurable=classifier_is_measurable,
                segmentation_is_sufficient=segmentation_is_sufficient,
                geometry_is_measurable=bool(
                    measurement_debug.get("geometry_is_measurable", False)
                ),
                measurement_succeeded=measurement_method not in (None, "none"),
                primary_length_px=primary_length_px,
                reason_codes=measurement_reasons_original,
                geometry_confidence=measurement_confidence,
                touch_border="touch_border" in measurement_reasons_original,
                adhesion_suspected=bool(
                    measurement_debug.get("adhesion_suspected", False)
                ),
                path_ambiguous=bool(measurement_debug.get("path_ambiguous", False)),
                no_trusted_measurement_path=(
                    "no_trusted_measurement_path" in measurement_reasons_original
                ),
                mask_abnormal=mask_abnormal,
                length_anomaly=False,
                p_measurable=outcome.final_probability,
                segmentation_confidence=instance.segmentation_confidence,
                path_score=measurement_debug.get("path_score"),
                path_score_gap=measurement_debug.get("path_score_gap"),
                path_turn_rate=measurement_debug.get("path_turn_rate"),
                curvature_ratio=measurement_debug.get("curvature_ratio"),
                config=AdmissionPolicyConfig(
                    mode=self._manifest.admission_policy.mode,
                    geometry_rescue_enabled=(
                        self._manifest.admission_policy.geometry_rescue_enabled
                    ),
                    min_rescue_probability=(
                        self._manifest.admission_policy.min_rescue_probability
                    ),
                    tier_b_probability_ceiling=(
                        self._manifest.admission_policy.tier_b_probability_ceiling
                    ),
                    tier_b_min_segmentation_confidence=(
                        self._manifest.admission_policy.tier_b_min_segmentation_confidence
                    ),
                    tier_b_min_path_score=(
                        self._manifest.admission_policy.tier_b_min_path_score
                    ),
                    tier_b_min_path_score_gap=(
                        self._manifest.admission_policy.tier_b_min_path_score_gap
                    ),
                    tier_b_max_path_turn_rate=(
                        self._manifest.admission_policy.tier_b_max_path_turn_rate
                    ),
                    tier_b_max_curvature_ratio=(
                        self._manifest.admission_policy.tier_b_max_curvature_ratio
                    ),
                ),
            )
            is_measurable = evaluation.is_measurable
            measurement_confidence = evaluation.geometry_confidence
            measurement_reasons = evaluation.reason_codes
            rescue_shadow = (
                {
                    "rescued": evaluation.rescued,
                    "blocked_by": evaluation.rescue_blocked_by,
                    "signals": evaluation.signals,
                }
                if evaluation.rescued or evaluation.rescue_blocked_by
                else None
            )

            fish.append(
                PipelineFish(
                    instance_id=instance.instance_id,
                    bbox_xyxy=instance.bbox_xyxy,
                    mask=instance.mask,
                    polygon_px=(
                        polygon_px
                        if polygon_px is not None
                        else np.empty((0, 2), dtype=np.float32)
                    ),
                    polygon_norm=polygon_norm or [],
                    segmentation_confidence=instance.segmentation_confidence,
                    single_measurable_probability=outcome.single_probability,
                    final_measurable_probability=outcome.final_probability,
                    is_measurable=is_measurable,
                    temporal_applied=outcome.applied,
                    temporal_policy=outcome.policy,
                    temporal_fallback_reason=outcome.fallback_reason,
                    temporal_history_count=outcome.history_count,
                    measurement_method=measurement_method,
                    measurement_confidence=measurement_confidence,
                    measurement_reasons=measurement_reasons,
                    visible_mask_length_px=visible_mask_length_px,
                    primary_length_px=primary_length_px,
                    measurement_debug=measurement_debug,
                    rescue_shadow=rescue_shadow,
                )
            )

        debug = {
            "manifest_id": self._manifest.manifest_id,
            "release_status": self._manifest.release_status,
            "fixture": (
                self._manifest.fixture.type if self._manifest.fixture else None
            ),
            "temporal_policy": outcomes[0].policy if outcomes else "disabled",
            "temporal_applied_count": sum(1 for outcome in outcomes if outcome.applied),
        }
        return FrameAnalysisOutput(
            width=width,
            height=height,
            fish=fish,
            debug=debug,
        )

    @staticmethod
    def _disabled_outcome(
        instance: FishInstance, probability: float
    ) -> Any:
        from app.models.ai.pipeline.contracts import TemporalOutcome

        return TemporalOutcome(
            instance_id=instance.instance_id,
            single_probability=float(probability),
            final_probability=float(probability),
            applied=False,
            policy="disabled",
            fallback_reason="disabled",
            history_count=0,
        )

    # ------------------------------------------------------------------
    # API 兼容映射（pipeline 内部结果 -> legacy raw detection dict）
    # ------------------------------------------------------------------

    def to_legacy_detections(self, output: FrameAnalysisOutput) -> List[Dict[str, Any]]:
        """把管线输出映射为 legacy `_build_detection_items` 可读的 dict 列表。"""
        detections: List[Dict[str, Any]] = []
        for fish in output.fish:
            x0, y0, x1, y1 = fish.bbox_xyxy
            detection: Dict[str, Any] = {
                "class_name": fish.class_name,
                "confidence": round(fish.segmentation_confidence, 4),
                "bbox": [float(x0), float(y0), float(x1 - x0), float(y1 - y0)],
                "length": (
                    round(float(fish.primary_length_px), 4)
                    if fish.primary_length_px is not None
                    else 0.0
                ),
                "mask_polygons": fish.polygon_norm,
                "measurement_method": fish.measurement_method,
                "measurement_confidence": fish.measurement_confidence,
                "measurement_reasons": fish.measurement_reasons,
                "visible_mask_length_px": fish.visible_mask_length_px,
                "is_measurable": fish.is_measurable,
                # 以下为可选 debug 字段（API 层裁剪，不影响既有字段）
                "instance_id": fish.instance_id,
                "seg_confidence": round(fish.segmentation_confidence, 4),
                "single_measurable_probability": round(
                    fish.single_measurable_probability, 6
                ),
                "final_measurable_probability": round(
                    fish.final_measurable_probability, 6
                ),
                "temporal_applied": fish.temporal_applied,
                "temporal_policy": fish.temporal_policy,
                "temporal_fallback_reason": fish.temporal_fallback_reason,
                "temporal_history_count": fish.temporal_history_count,
                "measurement_debug": fish.measurement_debug,
            }
            detections.append(detection)
        return detections
