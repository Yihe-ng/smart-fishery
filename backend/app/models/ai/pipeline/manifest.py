"""模型 Manifest：部署权威配置（路径/阈值/后处理/时序/测长/业务等）。

设计原则：
- 所有模型路径、imgsz、conf、NMS、类别语义、阈值、时序策略、窗口、batch size
  一律从 manifest 加载，禁止散落硬编码；
- 非法配置 fail fast（缺字段/类型错/数值越界直接抛错）；
- 当前所有条目必须标记 release_status=candidate（或 review），
  解析器对新增测长和业务字段 fail fast，避免配置与代码口径漂移。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Dict, List, Optional


SUPPORTED_SCHEMA_VERSION = 1
# 允许的发布状态：candidate/review 为开发态，final 为正式冻结（2026-08-08 授权）
ALLOWED_RELEASE_STATUSES = {"candidate", "review", "final"}
# 当前 fixture 类型：标记候选权重，禁止视为正式 release
FIXTURE_TYPE_CANDIDATE = "candidate_fixture"


@dataclass(frozen=True)
class SegmentationManifest:
    backend: str
    path: str
    imgsz: int
    conf: float
    nms_iou: float
    retina_masks: bool
    mask_policy: str
    class_names: List[str]
    secondary_review_area_ratio: float = 0.05
    min_confidence_for_measurement: float = 0.0
    sha256: Optional[str] = None  # 权重 SHA256（正式清单可追溯）


@dataclass(frozen=True)
class ClassifierManifest:
    backend: str
    path: str
    input_size: int
    positive_semantic: str
    threshold: float
    batch_size: int
    class_names: List[str]
    pretrained_path: Optional[str] = None  # 自定义头模型（如 V12 T1）需要的 backbone
    temperature: Optional[float] = None
    sha256: Optional[str] = None  # 权重 SHA256（正式清单可追溯）


@dataclass(frozen=True)
class CropManifest:
    margin_fraction_each_side: float
    bbox_scale: float
    tile_size: int
    padding_value: int
    mask_focus_outside_brightness: Optional[float] = None


@dataclass(frozen=True)
class TemporalManifest:
    enabled_for_image: bool
    enabled_for_video: bool
    policy: str
    window: int
    max_frame_gap: int
    fallback: str
    association: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MeasurementQualityManifest:
    """测长几何质量门槛；最终值必须由验收集证据确认。"""

    min_area_px: int = 60
    min_solidity: float = 0.55
    core_distance_fraction: float = 0.35
    min_core_pixels: int = 20
    min_axis_stability: float = 1.25
    straight_max_curvature_ratio: float = 1.18
    max_curvature_ratio: float = 1.60
    max_secondary_area_ratio: float = 0.25
    max_hole_area_ratio: float = 0.12
    small_hole_fill_ratio: float = 0.02
    max_highlight_ratio: float = 0.40
    max_endpoint_count: int = 8
    max_branch_count: int = 24
    min_path_ratio: float = 0.45
    min_path_score: float = 0.45
    min_path_score_gap: float = 0.06
    max_turn_rate: float = 0.55
    max_core_component_count: int = 2


@dataclass(frozen=True)
class MeasurementScaleManifest:
    """像素到估算厘米的场景先验；位置修正默认关闭。"""

    cm_per_pixel: float = 0.1
    position_correction_enabled: bool = False
    beta_x: float = 0.0
    beta_y: float = 0.0
    applicable_min_px: Optional[float] = None
    applicable_max_px: Optional[float] = None


@dataclass(frozen=True)
class BusinessManifest:
    """估算体长分档和石斑鱼经验估重公式。"""

    small_threshold_cm: float = 15.0
    large_threshold_cm: float = 25.0
    weight_coefficient_a: float = 0.0285
    weight_exponent_b: float = 2.937


@dataclass(frozen=True)
class AdmissionPolicyManifest:
    """A5 准入策略配置。

    - mode：strict（正式默认）| geometry_rescue（影子候选）；
    - geometry_rescue_enabled：是否启用几何救援影子计算（正式默认 False，
      启用后仅附加影子结果，不改变正式 API 输出）。
    """

    mode: str = "strict"
    geometry_rescue_enabled: bool = False
    min_rescue_probability: Optional[float] = None
    tier_b_probability_ceiling: Optional[float] = None
    tier_b_min_segmentation_confidence: Optional[float] = None
    tier_b_min_path_score: Optional[float] = None
    tier_b_min_path_score_gap: Optional[float] = None
    tier_b_max_path_turn_rate: Optional[float] = None
    tier_b_max_curvature_ratio: Optional[float] = None


@dataclass(frozen=True)
class MeasurementManifest:
    """测长算法、几何质量和单位换算配置。"""

    # 保留顶层字段，兼容既有测试和旧代码；正式 JSON 同时写入 scale。
    cm_per_pixel: float
    algorithm: str = "visible_centerline_hybrid"
    quality: MeasurementQualityManifest = field(default_factory=MeasurementQualityManifest)
    scale: MeasurementScaleManifest = field(default_factory=MeasurementScaleManifest)


@dataclass(frozen=True)
class FixtureManifest:
    type: str
    note: Optional[str] = None


@dataclass(frozen=True)
class ModelManifest:
    schema_version: int
    manifest_id: str
    release_status: str
    fixture: Optional[FixtureManifest]
    segmentation: SegmentationManifest
    classifier: ClassifierManifest
    crop: CropManifest
    temporal: TemporalManifest
    measurement: MeasurementManifest
    business: BusinessManifest = field(default_factory=BusinessManifest)
    admission_policy: AdmissionPolicyManifest = field(default_factory=AdmissionPolicyManifest)
    profile_revision: Optional[str] = None
    derived_from_manifest_id: Optional[str] = None
    description: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def is_candidate_fixture(self) -> bool:
        return (
            self.fixture is not None
            and self.fixture.type == FIXTURE_TYPE_CANDIDATE
        )


# ---------------------------------------------------------------------------
# 解析与校验
# ---------------------------------------------------------------------------


def _require_mapping(raw: Any, section: str) -> Dict[str, Any]:
    value = raw.get(section)
    if not isinstance(value, dict):
        raise ValueError(f"manifest 段 {section!r} 必须是对象")
    return value


def _require_bool(raw: Any, section: str, key: str) -> bool:
    value = raw.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"{section}.{key} 必须是布尔值")
    return value


def _require_int(
    raw: Any,
    section: str,
    key: str,
    *,
    minimum: int = 0,
    maximum: int | None = None,
) -> int:
    value = raw.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{section}.{key} 必须是整数")
    if value < minimum:
        raise ValueError(f"{section}.{key} 必须 >= {minimum}")
    if maximum is not None and value > maximum:
        raise ValueError(f"{section}.{key} 必须 <= {maximum}")
    return value


def _require_float(raw: Any, section: str, key: str, *, minimum: float, maximum: float) -> float:
    value = raw.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{section}.{key} 必须是数值")
    value = float(value)
    if not minimum <= value <= maximum:
        raise ValueError(f"{section}.{key} 必须在 [{minimum}, {maximum}] 内")
    return value


def _require_str(raw: Any, section: str, key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{section}.{key} 必须是非空字符串")
    return value.strip()


def _parse_segmentation(raw: Dict[str, Any]) -> SegmentationManifest:
    seg_raw = dict(raw)
    seg_raw.setdefault("secondary_review_area_ratio", 0.05)
    seg_raw.setdefault("min_confidence_for_measurement", 0.0)
    return SegmentationManifest(
        backend=_require_str(raw, "segmentation", "backend"),
        path=_require_str(raw, "segmentation", "path"),
        imgsz=_require_int(raw, "segmentation", "imgsz", minimum=64),
        conf=_require_float(raw, "segmentation", "conf", minimum=0.0, maximum=1.0),
        nms_iou=_require_float(raw, "segmentation", "nms_iou", minimum=0.0, maximum=1.0),
        retina_masks=_require_bool(raw, "segmentation", "retina_masks"),
        mask_policy=_require_str(raw, "segmentation", "mask_policy"),
        class_names=_require_str_list(raw, "segmentation", "class_names"),
        secondary_review_area_ratio=_require_float(
            seg_raw,
            "segmentation",
            "secondary_review_area_ratio",
            minimum=0.0,
            maximum=1.0,
        ),
        min_confidence_for_measurement=_require_float(
            seg_raw,
            "segmentation",
            "min_confidence_for_measurement",
            minimum=0.0,
            maximum=1.0,
        ),
        sha256=(
            _require_str(raw, "segmentation", "sha256")
            if raw.get("sha256") is not None
            else None
        ),
    )


def _parse_classifier(raw: Dict[str, Any]) -> ClassifierManifest:
    parsed = ClassifierManifest(
        backend=_require_str(raw, "classifier", "backend"),
        path=_require_str(raw, "classifier", "path"),
        input_size=_require_int(raw, "classifier", "input_size", minimum=16),
        positive_semantic=_require_str(raw, "classifier", "positive_semantic"),
        threshold=_require_float(raw, "classifier", "threshold", minimum=0.0, maximum=1.0),
        batch_size=_require_int(raw, "classifier", "batch_size", minimum=1),
        class_names=_require_str_list(raw, "classifier", "class_names"),
        pretrained_path=(
            _require_str(raw, "classifier", "pretrained_path")
            if raw.get("pretrained_path") is not None
            else None
        ),
        temperature=(
            _require_float(raw, "classifier", "temperature", minimum=1e-6, maximum=1e6)
            if raw.get("temperature") is not None
            else None
        ),
        sha256=(
            _require_str(raw, "classifier", "sha256")
            if raw.get("sha256") is not None
            else None
        ),
    )
    if parsed.backend == "ultralytics_yolo_cls_t1" and parsed.pretrained_path is None:
        raise ValueError("classifier.backend=ultralytics_yolo_cls_t1 需要 pretrained_path")
    if parsed.positive_semantic not in parsed.class_names:
        raise ValueError(
            f"classifier.positive_semantic={parsed.positive_semantic!r} "
            f"不在 class_names={parsed.class_names!r} 中"
        )
    return parsed


def _parse_crop(raw: Dict[str, Any]) -> CropManifest:
    return CropManifest(
        margin_fraction_each_side=_require_float(
            raw, "crop", "margin_fraction_each_side", minimum=0.0, maximum=1.0
        ),
        bbox_scale=_require_float(raw, "crop", "bbox_scale", minimum=1.0, maximum=10.0),
        tile_size=_require_int(raw, "crop", "tile_size", minimum=16),
        padding_value=_require_int(raw, "crop", "padding_value", minimum=0, maximum=255),
        mask_focus_outside_brightness=(
            _require_float(
                raw, "crop", "mask_focus_outside_brightness", minimum=0.0, maximum=1.0
            )
            if raw.get("mask_focus_outside_brightness") is not None
            else None
        ),
    )


def _parse_temporal(raw: Dict[str, Any]) -> TemporalManifest:
    policy = _require_str(raw, "temporal", "policy")
    if policy not in {"disabled", "causal_mean", "gated_causal"}:
        raise ValueError(
            f"temporal.policy={policy!r} 不支持，可选：disabled/causal_mean/gated_causal"
        )
    fallback = _require_str(raw, "temporal", "fallback")
    if fallback != "single":
        raise ValueError("temporal.fallback 当前仅支持 'single'（单帧概率回退）")
    return TemporalManifest(
        enabled_for_image=_require_bool(raw, "temporal", "enabled_for_image"),
        enabled_for_video=_require_bool(raw, "temporal", "enabled_for_video"),
        policy=policy,
        window=_require_int(raw, "temporal", "window", minimum=1),
        max_frame_gap=_require_int(raw, "temporal", "max_frame_gap", minimum=1),
        fallback=fallback,
        association=raw.get("association") or {},
    )


def _parse_measurement_quality(raw: Dict[str, Any]) -> MeasurementQualityManifest:
    """严格解析几何质量门槛，避免把未经确认的字符串或越界数值带入生产。"""
    defaults = MeasurementQualityManifest()
    int_bounds = {
        "min_area_px": (1, 10_000_000),
        "min_core_pixels": (1, 10_000_000),
        "max_endpoint_count": (0, 1000),
        "max_branch_count": (0, 1000),
        "max_core_component_count": (1, 100),
    }
    float_bounds = {
        "min_solidity": (0.0, 1.0),
        "core_distance_fraction": (0.0, 1.0),
        "straight_max_curvature_ratio": (0.0, 100.0),
        "max_curvature_ratio": (0.0, 100.0),
        "max_secondary_area_ratio": (0.0, 1.0),
        "max_hole_area_ratio": (0.0, 1.0),
        "small_hole_fill_ratio": (0.0, 1.0),
        "max_highlight_ratio": (0.0, 1.0),
        "min_path_ratio": (0.0, 1.0),
        "min_path_score": (0.0, 1.0),
        "min_path_score_gap": (0.0, 1.0),
        "max_turn_rate": (0.0, 1.0),
        "min_axis_stability": (0.0, 1_000_000.0),
    }
    values: Dict[str, Any] = {}
    for name, bounds in int_bounds.items():
        value = raw.get(name, getattr(defaults, name))
        values[name] = _require_int(
            {name: value}, "measurement.quality", name, minimum=bounds[0], maximum=bounds[1]
        )
    for name, bounds in float_bounds.items():
        value = raw.get(name, getattr(defaults, name))
        values[name] = _require_float(
            {name: value}, "measurement.quality", name, minimum=bounds[0], maximum=bounds[1]
        )
    return MeasurementQualityManifest(**values)


def _parse_measurement(raw: Dict[str, Any]) -> MeasurementManifest:
    """解析测长算法、质量和换算配置；兼容旧版顶层 cm_per_pixel。"""
    algorithm = str(raw.get("algorithm", "visible_centerline_hybrid")).strip()
    if algorithm not in {"visible_centerline_hybrid", "legacy_compat"}:
        raise ValueError(
            f"measurement.algorithm={algorithm!r} 不支持，可选：visible_centerline_hybrid/legacy_compat"
        )
    quality_raw = raw.get("quality") or {}
    if not isinstance(quality_raw, dict):
        raise ValueError("measurement.quality 必须是对象")
    scale_raw = raw.get("scale") or {}
    if not isinstance(scale_raw, dict):
        raise ValueError("measurement.scale 必须是对象")
    cm_value = scale_raw.get("cm_per_pixel", raw.get("cm_per_pixel", 0.1))
    cm_per_pixel = _require_float(
        {"cm_per_pixel": cm_value},
        "measurement.scale",
        "cm_per_pixel",
        minimum=1e-6,
        maximum=1e6,
    )
    position_enabled = scale_raw.get("position_correction_enabled", False)
    if not isinstance(position_enabled, bool):
        raise ValueError("measurement.scale.position_correction_enabled 必须是布尔值")
    beta_x = _require_float(
        {"beta_x": scale_raw.get("beta_x", 0.0)},
        "measurement.scale",
        "beta_x",
        minimum=-1e6,
        maximum=1e6,
    )
    beta_y = _require_float(
        {"beta_y": scale_raw.get("beta_y", 0.0)},
        "measurement.scale",
        "beta_y",
        minimum=-1e6,
        maximum=1e6,
    )
    optional_bounds: Dict[str, Optional[float]] = {}
    for name in ("applicable_min_px", "applicable_max_px"):
        value = scale_raw.get(name)
        optional_bounds[name] = (
            _require_float(
                {name: value}, "measurement.scale", name, minimum=0.0, maximum=1e9
            )
            if value is not None
            else None
        )
    scale = MeasurementScaleManifest(
        cm_per_pixel=cm_per_pixel,
        position_correction_enabled=position_enabled,
        beta_x=beta_x,
        beta_y=beta_y,
        applicable_min_px=optional_bounds["applicable_min_px"],
        applicable_max_px=optional_bounds["applicable_max_px"],
    )
    return MeasurementManifest(
        cm_per_pixel=cm_per_pixel,
        algorithm=algorithm,
        quality=_parse_measurement_quality(quality_raw),
        scale=scale,
    )


def _parse_admission_policy(raw: Any) -> AdmissionPolicyManifest:
    """解析准入策略配置（缺失时使用 strict + 禁用救援的正式默认值）。"""
    if raw is None:
        return AdmissionPolicyManifest()
    if not isinstance(raw, dict):
        raise ValueError("admission_policy 必须是对象")
    mode = str(raw.get("mode", "strict")).strip()
    if mode not in {"strict", "geometry_rescue"}:
        raise ValueError(
            f"admission_policy.mode={mode!r} 不支持，可选：strict/geometry_rescue"
        )
    enabled = raw.get("geometry_rescue_enabled", False)
    if not isinstance(enabled, bool):
        raise ValueError("admission_policy.geometry_rescue_enabled 必须是布尔值")

    def optional_float(key: str, minimum: float, maximum: float) -> Optional[float]:
        if raw.get(key) is None:
            return None
        return _require_float(
            raw, "admission_policy", key, minimum=minimum, maximum=maximum
        )

    floor = optional_float("min_rescue_probability", 0.0, 1.0)
    ceiling = optional_float("tier_b_probability_ceiling", 0.0, 1.0)
    tier_values = {
        "tier_b_min_segmentation_confidence": optional_float(
            "tier_b_min_segmentation_confidence", 0.0, 1.0
        ),
        "tier_b_min_path_score": optional_float("tier_b_min_path_score", 0.0, 1.0),
        "tier_b_min_path_score_gap": optional_float(
            "tier_b_min_path_score_gap", 0.0, 1.0
        ),
        "tier_b_max_path_turn_rate": optional_float(
            "tier_b_max_path_turn_rate", 0.0, 1.0
        ),
        "tier_b_max_curvature_ratio": optional_float(
            "tier_b_max_curvature_ratio", 0.0, 100.0
        ),
    }
    if ceiling is not None:
        if floor is None or floor >= ceiling:
            raise ValueError(
                "admission_policy.min_rescue_probability 必须小于 tier_b_probability_ceiling"
            )
        missing = [key for key, value in tier_values.items() if value is None]
        if missing:
            raise ValueError(
                "admission_policy 启用 tier_b 时缺少参数: " + ", ".join(missing)
            )

    return AdmissionPolicyManifest(
        mode=mode,
        geometry_rescue_enabled=enabled,
        min_rescue_probability=floor,
        tier_b_probability_ceiling=ceiling,
        **tier_values,
    )


def _parse_business(raw: Dict[str, Any]) -> BusinessManifest:
    """解析估算体长分档和估重公式。"""
    if not isinstance(raw, dict):
        raise ValueError("business 必须是对象")
    small = _require_float(
        {"small_threshold_cm": raw.get("small_threshold_cm", 15.0)},
        "business",
        "small_threshold_cm",
        minimum=0.0,
        maximum=1e6,
    )
    large = _require_float(
        {"large_threshold_cm": raw.get("large_threshold_cm", 25.0)},
        "business",
        "large_threshold_cm",
        minimum=small,
        maximum=1e6,
    )
    coefficient = _require_float(
        {"weight_coefficient_a": raw.get("weight_coefficient_a", 0.0285)},
        "business",
        "weight_coefficient_a",
        minimum=0.0,
        maximum=1e6,
    )
    exponent = _require_float(
        {"weight_exponent_b": raw.get("weight_exponent_b", 2.937)},
        "business",
        "weight_exponent_b",
        minimum=0.0,
        maximum=20.0,
    )
    return BusinessManifest(
        small_threshold_cm=small,
        large_threshold_cm=large,
        weight_coefficient_a=coefficient,
        weight_exponent_b=exponent,
    )


def _require_str_list(raw: Dict[str, Any], section: str, key: str) -> List[str]:
    values = raw.get(key)
    if not isinstance(values, list) or not values:
        raise ValueError(f"{section}.{key} 必须是非空数组")
    if not all(isinstance(item, str) and item.strip() for item in values):
        raise ValueError(f"{section}.{key} 必须全是非空字符串")
    return [str(item).strip() for item in values]


def parse_manifest(raw: Dict[str, Any]) -> ModelManifest:
    """从字典解析并严格校验 manifest（fail fast）。"""
    schema_version = _require_int(raw, "manifest", "schema_version", minimum=1)
    if schema_version != SUPPORTED_SCHEMA_VERSION:
        raise ValueError(f"不支持的 manifest schema_version={schema_version}，当前仅支持 1")

    release_status = _require_str(raw, "manifest", "release_status")
    if release_status not in ALLOWED_RELEASE_STATUSES:
        raise ValueError(
            f"release_status={release_status!r} 不允许；"
            f"部署侧禁止 final，仅允许 {sorted(ALLOWED_RELEASE_STATUSES)}"
        )

    fixture_raw = raw.get("fixture")
    fixture: Optional[FixtureManifest] = None
    if fixture_raw is not None:
        fixture = FixtureManifest(
            type=_require_str(fixture_raw, "fixture", "type"),
            note=(
                str(fixture_raw["note"])
                if fixture_raw.get("note") is not None
                else None
            ),
        )

    return ModelManifest(
        schema_version=schema_version,
        manifest_id=_require_str(raw, "manifest", "manifest_id"),
        release_status=release_status,
        fixture=fixture,
        segmentation=_parse_segmentation(_require_mapping(raw, "segmentation")),
        classifier=_parse_classifier(_require_mapping(raw, "classifier")),
        crop=_parse_crop(_require_mapping(raw, "crop")),
        temporal=_parse_temporal(_require_mapping(raw, "temporal")),
        measurement=_parse_measurement(_require_mapping(raw, "measurement")),
        business=_parse_business(raw.get("business") or {}),
        admission_policy=_parse_admission_policy(raw.get("admission_policy")),
        profile_revision=(
            _require_str(raw, "manifest", "profile_revision")
            if raw.get("profile_revision") is not None
            else None
        ),
        derived_from_manifest_id=(
            _require_str(raw, "manifest", "derived_from_manifest_id")
            if raw.get("derived_from_manifest_id") is not None
            else None
        ),
        description=(
            str(raw["description"]) if raw.get("description") is not None else None
        ),
        extra={key: value for key, value in raw.items() if key not in _KNOWN_KEYS},
    )


_KNOWN_KEYS = {
    "schema_version",
    "manifest_id",
    "release_status",
    "profile_revision",
    "derived_from_manifest_id",
    "fixture",
    "segmentation",
    "classifier",
    "crop",
    "temporal",
    "measurement",
    "business",
    "admission_policy",
    "description",
}


def _backend_root() -> Path:
    """backend 根目录（manifest.py 位于 backend/app/models/ai/pipeline/ 下）。"""
    return Path(__file__).resolve().parents[4]


def _resolve_model_path(value: str) -> str:
    """相对路径以 backend 根为基准解析；绝对路径原样返回。"""
    path = Path(value)
    if path.is_absolute():
        return str(path)
    return str((_backend_root() / path).resolve())


def _resolve_manifest_paths(manifest: ModelManifest) -> ModelManifest:
    """把 manifest 中模型相关相对路径统一解析为绝对路径。"""
    seg = replace(manifest.segmentation, path=_resolve_model_path(manifest.segmentation.path))
    cls_kwargs = {
        "path": _resolve_model_path(manifest.classifier.path),
        "pretrained_path": (
            _resolve_model_path(manifest.classifier.pretrained_path)
            if manifest.classifier.pretrained_path is not None
            else None
        ),
    }
    classifier = replace(manifest.classifier, **cls_kwargs)
    return replace(manifest, segmentation=seg, classifier=classifier)


def load_manifest(path: str | Path) -> ModelManifest:
    """从 JSON 文件加载并校验 manifest。"""
    manifest_path = Path(path)
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"manifest 文件不存在: {manifest_path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"manifest JSON 解析失败: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError("manifest 顶层必须是 JSON 对象")
    return _resolve_manifest_paths(parse_manifest(raw))
