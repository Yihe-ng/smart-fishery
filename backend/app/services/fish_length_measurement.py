"""基于分割 mask 的投影可见中心线测长。

设计意图：先从 mask 中提取鱼身厚核心，降低侧鳍对主体方向的影响；再在骨架图
中评价候选路径，排除横向、细短和急转弯分支；弯鱼使用可信中心路径，直鱼允许
使用稳健主体 PCA；两种方法都不可靠时返回不可测，不强行制造长度。

该模块不把像素长度宣称为真实物理长度。厘米换算、业务分档和估重由 manifest/API
另行管理；这里的生产输出只负责像素测长和可解释的几何质量结果。
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import cv2
import numpy as np
from skimage.morphology import skeletonize


@dataclass(frozen=True)
class MeasurementConfig:
    """测长算法和质量门槛配置。

    配置字段会由正式 manifest 提供；这里的默认值只用于旧调用方兼容和单元测试。
    这些值是候选起点，不代表已经通过约 100 条实例的最终验收。
    """

    algorithm: str = "visible_centerline_hybrid"
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
    # gap 竞争者判定：次佳路径与最佳路径重合度 >= 该值且长度偏离 <= 容差时，
    # 视为同一条路径的分叉变体（伪竞争者），跳过不参与 gap 比较。
    gap_competitor_max_iou: float = 0.7
    gap_competitor_length_tolerance: float = 0.15


DEFAULT_MEASUREMENT_CONFIG = MeasurementConfig()


@dataclass
class MeasurementResult:
    """单条鱼的像素测长、质量特征和失败原因。

    当 `is_measurable=False` 时，`primary_length_px` 仅作为离线调试参考，业务层不
    应把它换算成体长；生产回退是不可测，而不是完整 mask 的 minAreaRect 长边。
    """

    primary_length_px: float = 0.0
    visible_mask_length_px: float = 0.0
    measurement_method: str = "none"  # centerline_arc | robust_core_pca | none
    is_measurable: bool = False
    reasons: List[str] = field(default_factory=list)
    curvature_ratio: float = 1.0
    straightness_ratio: float = 1.0
    main_axis_length_px: float = 0.0
    centerline_length_px: float = 0.0
    area: float = 0.0
    solidity: float = 1.0
    touch_border: bool = False
    endpoint_count: int = 0
    branch_count: int = 0
    main_path_ratio: float = 1.0
    geometry_confidence: float = 0.0
    secondary_component_ratio: float = 0.0
    hole_count: int = 0
    hole_area_ratio: float = 0.0
    highlight_ratio: float = 0.0
    core_area_ratio: float = 0.0
    core_component_count: int = 0
    axis_stability: float = 0.0
    path_score: float = 0.0
    path_score_gap: float = 0.0
    path_turn_rate: float = 0.0
    adhesion_suspected: bool = False
    path_ambiguous: bool = False
    path_points: List[List[float]] = field(default_factory=list)
    quality_features: Dict[str, float] = field(default_factory=dict)


def resolve_measurement_config(value: Any = None) -> MeasurementConfig:
    """把 manifest 的嵌套配置转换为测长服务可用配置。

    旧 manifest 只有 `measurement.cm_per_pixel` 时仍能被读取；算法字段采用候选默认
    值，正式 manifest 在策略确认后再写入明确版本和门槛。
    """
    if value is None:
        return DEFAULT_MEASUREMENT_CONFIG
    if isinstance(value, MeasurementConfig):
        return value

    quality = getattr(value, "quality", value)
    algorithm = str(getattr(value, "algorithm", DEFAULT_MEASUREMENT_CONFIG.algorithm))
    kwargs: Dict[str, Any] = {"algorithm": algorithm}
    for name in MeasurementConfig.__dataclass_fields__:
        if name == "algorithm":
            continue
        default = getattr(DEFAULT_MEASUREMENT_CONFIG, name)
        candidate = getattr(quality, name, default)
        if isinstance(default, int):
            kwargs[name] = int(candidate)
        else:
            kwargs[name] = float(candidate)
    return MeasurementConfig(**kwargs)


def measure_fish_length(
    polygon_px: np.ndarray,
    image_width: int,
    image_height: int,
    *,
    mask: Optional[np.ndarray] = None,
    rgb_image: Optional[np.ndarray] = None,
    config: Any = None,
) -> MeasurementResult:
    """测量单条鱼的吻端到可见尾鳍末端投影长度。

    主要输入是 mask 多边形；管线若已有全分辨率 bool mask，应通过 `mask` 传入，
    这样孔洞、次连通域和 RGB 高亮特征不会因重新栅格化而丢失。函数先检查主体
    核心和图像质量，再选择 `centerline_arc` 或 `robust_core_pca`。骨架端点歧义、
    疑似黏连、核心被孔洞破坏、边界截断或极小 mask 都会进入不可测出口。

    返回值中的 `path_points` 和质量字段供离线报告使用；正式前端不展示中心线。
    """
    cfg = resolve_measurement_config(config)
    if image_width <= 0 or image_height <= 0:
        return MeasurementResult(reasons=["invalid_image_shape"])
    if polygon_px is None or len(polygon_px) < 3:
        return MeasurementResult(reasons=["polygon_too_few_points"])

    binary_mask = _prepare_mask(mask, polygon_px, image_width, image_height)
    area = int(cv2.countNonZero(binary_mask))
    if area < cfg.min_area_px:
        return MeasurementResult(area=area, reasons=["area_too_small"], quality_features={"area": float(area)})

    primary_mask, secondary_ratio = _largest_component(binary_mask)
    contour, hull = _extract_largest_contour(primary_mask)
    if contour is None or hull is None:
        return MeasurementResult(area=area, reasons=["contour_extraction_failed"])

    primary_area = float(cv2.countNonZero(primary_mask))
    solidity = _compute_solidity(contour, hull, primary_area)
    touch_border = _touches_image_border(primary_mask)
    hole_count, hole_area_ratio, filled_mask = _analyse_and_fill_holes(primary_mask, cfg)
    highlight_ratio = _highlight_ratio(rgb_image, primary_mask)

    distance = cv2.distanceTransform((filled_mask > 0).astype(np.uint8), cv2.DIST_L2, 5)
    core_mask, core_area_ratio, core_component_count = _extract_body_core(distance, filled_mask, cfg)
    axis, axis_stability, core_pca_length = _thickness_weighted_axis_length(
        distance,
        filled_mask,
        core_mask,
    )

    centerline_length, path_info = _compute_scored_centerline(
        filled_mask,
        distance,
        axis,
        cfg,
    )
    endpoint_count = int(path_info.get("endpoint_count", 0))
    branch_count = int(path_info.get("branch_count", 0))
    total_skeleton_length = float(path_info.get("total_skeleton_length", 0.0))
    main_path_ratio = float(path_info.get("main_path_ratio", 0.0))
    path_score = float(path_info.get("path_score", 0.0))
    path_score_gap = float(path_info.get("path_score_gap", 0.0))
    path_turn_rate = float(path_info.get("path_turn_rate", 0.0))
    path_points = path_info.get("path_points", [])

    curvature_ratio = (
        centerline_length / max(core_pca_length, 1.0)
        if centerline_length > 0 and core_pca_length > 0
        else 1.0
    )
    straightness_ratio = 1.0 / max(curvature_ratio, 1e-6)
    path_ambiguous = (
        centerline_length <= 0
        or path_score < cfg.min_path_score
        or path_score_gap < cfg.min_path_score_gap
    )
    adhesion_suspected = (
        secondary_ratio > cfg.max_secondary_area_ratio
        or core_component_count > cfg.max_core_component_count
    )

    reasons: List[str] = []
    if touch_border:
        reasons.append("touch_border")
    if solidity < cfg.min_solidity:
        reasons.append("low_solidity")
    if secondary_ratio > cfg.max_secondary_area_ratio:
        reasons.append("adhesion_secondary_component")
    if hole_area_ratio > cfg.max_hole_area_ratio:
        reasons.append("large_or_core_cutting_hole")
    if highlight_ratio > cfg.max_highlight_ratio:
        reasons.append("high_highlight_risk")
    if core_component_count > cfg.max_core_component_count:
        reasons.append("multiple_body_cores")
    if endpoint_count > cfg.max_endpoint_count:
        reasons.append("too_many_endpoints")
    if branch_count > cfg.max_branch_count:
        reasons.append("too_many_branches")
    if path_turn_rate > cfg.max_turn_rate:
        reasons.append("path_turning_too_high")
    if main_path_ratio < cfg.min_path_ratio and centerline_length > 0:
        reasons.append("low_main_path_ratio")
    if curvature_ratio > cfg.max_curvature_ratio:
        reasons.append("curvature_too_high")
    if path_ambiguous:
        reasons.append("path_ambiguous")

    # 可信路径优先；只有近似直鱼且厚核心方向稳定时才允许 PCA 回退。
    if not path_ambiguous and centerline_length > 0:
        measurement_method = "centerline_arc"
        primary_length = centerline_length
    elif (
        axis is not None
        and axis_stability >= cfg.min_axis_stability
        and core_pca_length > 0
        and curvature_ratio <= cfg.straight_max_curvature_ratio
    ):
        measurement_method = "robust_core_pca"
        primary_length = core_pca_length
        # PCA 回退必须明确标记，不能与可信弯曲中心线混为一谈。
        reasons.append("centerline_fallback_core_pca")
    else:
        measurement_method = "none"
        primary_length = 0.0
        reasons.append("no_trusted_measurement_path")

    blocking_reasons = {
        "touch_border",
        "low_solidity",
        "adhesion_secondary_component",
        "large_or_core_cutting_hole",
        "high_highlight_risk",
        "multiple_body_cores",
        "too_many_endpoints",
        "too_many_branches",
        "path_turning_too_high",
        "low_main_path_ratio",
        "curvature_too_high",
        "no_trusted_measurement_path",
    }
    # 对近似直鱼，路径候选歧义正是允许进入稳健主体 PCA 回退的原因；PCA 已经
    # 通过厚度加权轴稳定性和曲折度门槛时，不应再次被同一个原因无条件阻断。
    # 中心线方案仍把 path_ambiguous 视为阻断，避免把不确定路径换算成业务长度。
    if measurement_method != "robust_core_pca":
        blocking_reasons.add("path_ambiguous")
    is_measurable = bool(primary_length > 0 and not blocking_reasons.intersection(reasons))
    geometry_confidence = _geometry_confidence(
        is_measurable=is_measurable,
        solidity=solidity,
        axis_stability=axis_stability,
        path_score=path_score,
        path_score_gap=path_score_gap,
        main_path_ratio=main_path_ratio,
        hole_area_ratio=hole_area_ratio,
        secondary_ratio=secondary_ratio,
    )
    quality_features = {
        "area": primary_area,
        "solidity": float(solidity),
        "secondary_component_ratio": float(secondary_ratio),
        "hole_area_ratio": float(hole_area_ratio),
        "highlight_ratio": float(highlight_ratio),
        "core_area_ratio": float(core_area_ratio),
        "core_component_count": float(core_component_count),
        "axis_stability": float(axis_stability),
        "path_score": float(path_score),
        "path_score_gap": float(path_score_gap),
        "path_turn_rate": float(path_turn_rate),
    }
    return MeasurementResult(
        primary_length_px=float(primary_length),
        visible_mask_length_px=float(centerline_length or core_pca_length or 0.0),
        measurement_method=measurement_method,
        is_measurable=is_measurable,
        reasons=_unique_reasons(reasons),
        curvature_ratio=round(curvature_ratio, 4),
        straightness_ratio=round(straightness_ratio, 4),
        main_axis_length_px=round(core_pca_length, 4),
        centerline_length_px=round(centerline_length, 4),
        area=primary_area,
        solidity=round(solidity, 4),
        touch_border=touch_border,
        endpoint_count=endpoint_count,
        branch_count=branch_count,
        main_path_ratio=round(main_path_ratio, 4),
        geometry_confidence=round(geometry_confidence, 4),
        secondary_component_ratio=round(secondary_ratio, 4),
        hole_count=hole_count,
        hole_area_ratio=round(hole_area_ratio, 4),
        highlight_ratio=round(highlight_ratio, 4),
        core_area_ratio=round(core_area_ratio, 4),
        core_component_count=core_component_count,
        axis_stability=round(axis_stability, 4),
        path_score=round(path_score, 4),
        path_score_gap=round(path_score_gap, 4),
        path_turn_rate=round(path_turn_rate, 4),
        adhesion_suspected=adhesion_suspected,
        path_ambiguous=path_ambiguous,
        path_points=path_points,
        quality_features=quality_features,
    )


def _prepare_mask(
    mask: Optional[np.ndarray],
    polygon_px: np.ndarray,
    image_width: int,
    image_height: int,
) -> np.ndarray:
    """优先使用真实全分辨率 mask，否则栅格化 polygon。"""
    if mask is not None:
        binary = np.asarray(mask)
        if binary.ndim == 3:
            binary = binary[..., 0]
        if binary.shape != (image_height, image_width):
            binary = cv2.resize(
                (binary > 0).astype(np.uint8),
                (image_width, image_height),
                interpolation=cv2.INTER_NEAREST,
            )
        return ((binary > 0).astype(np.uint8) * 255)
    result = np.zeros((image_height, image_width), dtype=np.uint8)
    points = np.asarray(polygon_px).reshape(-1, 1, 2).astype(np.int32)
    cv2.fillPoly(result, [points], 255)
    return result


def _largest_component(mask: np.ndarray) -> Tuple[np.ndarray, float]:
    """提取主体连通域并记录次连通域比例，用于提示疑似黏连。"""
    count, labels, stats, _ = cv2.connectedComponentsWithStats((mask > 0).astype(np.uint8), 8)
    if count <= 1:
        return mask.copy(), 0.0
    areas = stats[1:, cv2.CC_STAT_AREA]
    primary_index = int(np.argmax(areas)) + 1
    primary_area = float(areas[primary_index - 1])
    secondary_area = float(areas.sum() - primary_area)
    primary = np.where(labels == primary_index, 255, 0).astype(np.uint8)
    return primary, secondary_area / max(primary_area, 1.0)


def _extract_largest_contour(
    mask: np.ndarray,
) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None, None
    contour = max(contours, key=cv2.contourArea)
    return contour, cv2.convexHull(contour)


def _compute_solidity(contour: np.ndarray, hull: np.ndarray, mask_area: float) -> float:
    contour_area = float(cv2.contourArea(contour))
    hull_area = float(cv2.contourArea(hull))
    if hull_area <= 0:
        return 1.0
    # 使用 mask 面积而不是仅 contour 面积，避免小孔洞使指标失真。
    return max(0.0, min(1.0, mask_area / hull_area))


def _touches_image_border(mask: np.ndarray, margin: int = 1) -> bool:
    h, w = mask.shape
    if h <= margin * 2 or w <= margin * 2:
        return True
    return bool(
        mask[:margin, :].any()
        or mask[-margin:, :].any()
        or mask[:, :margin].any()
        or mask[:, -margin:].any()
    )


def _analyse_and_fill_holes(
    mask: np.ndarray,
    config: MeasurementConfig,
) -> Tuple[int, float, np.ndarray]:
    """识别内部孔洞；小孔仅用于受限填补，大孔保留为不可测证据。"""
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    if hierarchy is None:
        return 0, 0.0, mask.copy()
    hierarchy = hierarchy[0]
    outer_area = max(float(cv2.countNonZero(mask)), 1.0)
    hole_count = 0
    hole_area = 0.0
    filled = mask.copy()
    for index, contour in enumerate(contours):
        parent = int(hierarchy[index][3])
        if parent < 0:
            continue
        area = float(cv2.contourArea(contour))
        hole_count += 1
        hole_area += area
        if area / outer_area <= config.small_hole_fill_ratio:
            cv2.drawContours(filled, [contour], -1, 255, thickness=-1)
    return hole_count, hole_area / outer_area, filled


def _highlight_ratio(rgb_image: Optional[np.ndarray], mask: np.ndarray) -> float:
    """统计 mask 内高亮低饱和像素，仅作为反光风险特征。"""
    if rgb_image is None:
        return 0.0
    image = np.asarray(rgb_image)
    if image.ndim != 3 or image.shape[2] < 3:
        return 0.0
    if image.shape[:2] != mask.shape:
        image = cv2.resize(image, (mask.shape[1], mask.shape[0]), interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(image[..., :3].astype(np.uint8), cv2.COLOR_RGB2HSV)
    inside = mask > 0
    if not inside.any():
        return 0.0
    highlight = (hsv[..., 2] >= 245) & (hsv[..., 1] <= 45)
    return float((highlight & inside).sum() / max(int(inside.sum()), 1))


def _extract_body_core(
    distance: np.ndarray,
    mask: np.ndarray,
    config: MeasurementConfig,
) -> Tuple[np.ndarray, float, int]:
    """以距离变换厚度提取主体核心，降低侧鳍和细长噪声的方向影响。"""
    max_distance = float(distance.max())
    if max_distance <= 0:
        return np.zeros_like(mask), 0.0, 0
    threshold = max_distance * config.core_distance_fraction
    core = np.where(distance >= threshold, 255, 0).astype(np.uint8)
    if int(cv2.countNonZero(core)) < config.min_core_pixels:
        # 极细鱼体仍保留厚度最大的像素，后续 axis_stability 会决定能否回退。
        flat_indices = np.argsort(distance[mask > 0].ravel())[::-1]
        mask_indices = np.column_stack(np.where(mask > 0))
        keep = mask_indices[flat_indices[: config.min_core_pixels]]
        core = np.zeros_like(mask)
        core[keep[:, 0], keep[:, 1]] = 255
    count, labels, stats, _ = cv2.connectedComponentsWithStats((core > 0).astype(np.uint8), 8)
    core_areas = stats[1:, cv2.CC_STAT_AREA] if count > 1 else np.array([], dtype=np.int32)
    significant = int(np.sum(core_areas >= max(3, config.min_core_pixels * 0.12)))
    return core, float(cv2.countNonZero(core) / max(cv2.countNonZero(mask), 1)), significant


def _thickness_weighted_axis_length(
    distance: np.ndarray,
    mask: np.ndarray,
    core_mask: np.ndarray,
) -> Tuple[Optional[np.ndarray], float, float]:
    """用厚度平方加权 PCA 得到主体方向和稳健投影长度。"""
    rows, cols = np.where(mask > 0)
    if len(rows) < 3:
        return None, 0.0, 0.0
    points = np.column_stack((cols.astype(np.float64), rows.astype(np.float64)))
    weights = np.maximum(distance[rows, cols].astype(np.float64), 1e-3) ** 2
    center = np.average(points, axis=0, weights=weights)
    centered = points - center
    covariance = (centered * weights[:, None]).T @ centered / max(weights.sum(), 1.0)
    try:
        eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    except np.linalg.LinAlgError:
        return None, 0.0, 0.0
    order = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[order]
    axis = eigenvectors[:, order[0]].astype(np.float64)
    axis /= max(float(np.linalg.norm(axis)), 1e-9)
    stability = float(eigenvalues[0] / max(eigenvalues[1], 1e-6))
    projections = centered @ axis
    # 用距离权重分位数抑制侧鳍远端少量像素，不使用 minAreaRect 生产回退。
    low = _weighted_quantile(projections, weights, 0.01)
    high = _weighted_quantile(projections, weights, 0.99)
    length = max(0.0, high - low)
    if int(cv2.countNonZero(core_mask)) < 3:
        return axis, stability, length
    return axis, stability, length


def _weighted_quantile(values: np.ndarray, weights: np.ndarray, quantile: float) -> float:
    order = np.argsort(values)
    sorted_values = values[order]
    sorted_weights = np.maximum(weights[order], 1e-9)
    cumulative = np.cumsum(sorted_weights)
    position = float(np.clip(quantile, 0.0, 1.0) * cumulative[-1])
    return float(np.interp(position, cumulative, sorted_values))


def _compute_scored_centerline(
    mask: np.ndarray,
    distance: np.ndarray,
    axis: Optional[np.ndarray],
    config: MeasurementConfig,
) -> Tuple[float, Dict[str, Any]]:
    """构建骨架图并评分端点路径，排除侧鳍样细短横向分支。

    这里仍使用 8 邻接像素图，但不再直接取最远端点。每一对端点都计算轴向推进、
    中央厚度、主路径占比和转角惩罚；得分接近时返回 path_ambiguous，避免把侧鳍
    误当成吻端或尾端。
    """
    info: Dict[str, Any] = {
        "endpoint_count": 0,
        "branch_count": 0,
        "total_skeleton_length": 0.0,
        "main_path_ratio": 0.0,
        "path_score": 0.0,
        "path_score_gap": 0.0,
        "path_turn_rate": 0.0,
        "path_points": [],
    }
    try:
        ys, xs = np.where(mask > 0)
        if not len(xs):
            return 0.0, info
        y0, y1 = int(ys.min()), int(ys.max()) + 1
        x0, x1 = int(xs.min()), int(xs.max()) + 1
        sub = skeletonize(mask[y0:y1, x0:x1] > 0)
        skeleton = np.zeros_like(mask, dtype=bool)
        skeleton[y0:y1, x0:x1] = sub
    except Exception:
        return 0.0, info
    pixels = [tuple(int(value) for value in point) for point in np.column_stack(np.where(skeleton))]
    if len(pixels) < 2:
        return 0.0, info
    pixel_set = set(pixels)
    endpoints: List[Tuple[int, int]] = []
    branch_points: List[Tuple[int, int]] = []
    for row, col in pixels:
        neighbors = _neighbors(row, col, pixel_set)
        if len(neighbors) == 1:
            endpoints.append((row, col))
        elif len(neighbors) >= 3:
            branch_points.append((row, col))
    info["endpoint_count"] = len(endpoints)
    info["branch_count"] = len(branch_points)
    total_length = _skeleton_total_length(pixel_set)
    info["total_skeleton_length"] = total_length
    if len(endpoints) < 2:
        return 0.0, info

    candidates: List[Dict[str, Any]] = []
    candidate_pairs = itertools.combinations(endpoints, 2)
    for start, goal in candidate_pairs:
        path = _bfs_shortest_path(pixel_set, start, goal)
        if path is None or len(path) < 2:
            continue
        arc_length = _polyline_length_8connected(path)
        if arc_length <= 0:
            continue
        score, details = _score_path(path, arc_length, total_length, distance, axis)
        extended_path = _extend_path_to_visible_boundary(path, mask)
        extended_length = _polyline_length_8connected(extended_path)
        candidates.append(
            {
                "score": score,
                "arc_length": extended_length,
                "path": extended_path,
                **details,
            }
        )
    if not candidates:
        return 0.0, info
    candidates.sort(key=lambda item: item["score"], reverse=True)
    best = candidates[0]
    
    best_pixels = set(best["path"])
    best_length = float(best["arc_length"])
    competitor_score = 0.0
    competitor_index = None
    
    for index, cand in enumerate(candidates[1:], start=1):
        cand_pixels = set(cand["path"])
        intersection = len(best_pixels & cand_pixels)
        union = len(best_pixels | cand_pixels)
        iou = intersection / max(union, 1)
        length_ratio = float(cand["arc_length"]) / max(best_length, 1e-6)
        length_deviation = abs(1.0 - length_ratio)
        
        if (
            iou < config.gap_competitor_max_iou
            or length_deviation > config.gap_competitor_length_tolerance
        ):
            competitor_score = float(cand["score"])
            competitor_index = index
            break
    
    gap = float(best["score"]) - competitor_score
    
    info.update(
        {
            "main_path_ratio": min(1.0, best_length / max(total_length, 1.0)),
            "path_score": float(best["score"]),
            "path_score_gap": gap,
            "path_turn_rate": float(best["turn_rate"]),
            "path_points": [[float(col), float(row)] for row, col in best["path"]],
            "gap_competitor_index": competitor_index,
        }
    )
    return best_length, info


def _neighbors(row: int, col: int, pixel_set: set[Tuple[int, int]]) -> List[Tuple[int, int]]:
    return [
        (row + dr, col + dc)
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
        if (dr != 0 or dc != 0) and (row + dr, col + dc) in pixel_set
    ]


def _skeleton_total_length(pixel_set: set[Tuple[int, int]]) -> float:
    total = 0.0
    for row, col in pixel_set:
        for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
            if (row + dr, col + dc) in pixel_set:
                total += math.hypot(dr, dc)
    return total


def _score_path(
    path: List[Tuple[int, int]],
    arc_length: float,
    total_length: float,
    distance: np.ndarray,
    axis: Optional[np.ndarray],
) -> Tuple[float, Dict[str, float]]:
    start = np.array([path[0][1], path[0][0]], dtype=np.float64)
    end = np.array([path[-1][1], path[-1][0]], dtype=np.float64)
    direction = end - start
    direction /= max(float(np.linalg.norm(direction)), 1e-6)
    axial_progress = 0.5
    if axis is not None:
        axial_progress = abs(float(np.dot(direction, axis)))
    thickness_values = np.array([distance[row, col] for row, col in path], dtype=np.float64)
    thickness_score = float(np.clip(thickness_values.mean() / max(float(distance.max()), 1e-6), 0.0, 1.0))
    path_ratio = min(1.0, arc_length / max(total_length, 1.0))
    turn_rate = _path_turn_rate(path)
    turn_score = max(0.0, 1.0 - min(1.0, turn_rate))
    # 中央厚度和主路径占比让细短侧鳍分支天然降分。
    score = 0.40 * axial_progress + 0.25 * thickness_score + 0.20 * path_ratio + 0.15 * turn_score
    return float(score), {
        "turn_rate": float(turn_rate),
        "path_ratio": float(path_ratio),
        "axial_progress": float(axial_progress),
        "thickness_score": float(thickness_score),
    }


def _path_turn_rate(path: Sequence[Tuple[int, int]]) -> float:
    if len(path) < 4:
        return 0.0
    turns = 0.0
    samples = 0
    for index in range(1, len(path) - 1):
        before = np.array([path[index][1] - path[index - 1][1], path[index][0] - path[index - 1][0]], dtype=np.float64)
        after = np.array([path[index + 1][1] - path[index][1], path[index + 1][0] - path[index][0]], dtype=np.float64)
        before_norm = float(np.linalg.norm(before))
        after_norm = float(np.linalg.norm(after))
        if before_norm <= 0 or after_norm <= 0:
            continue
        cosine = float(np.clip(np.dot(before, after) / (before_norm * after_norm), -1.0, 1.0))
        turns += abs(math.acos(cosine)) / math.pi
        samples += 1
    return turns / max(samples, 1)


def _extend_path_to_visible_boundary(
    path: List[Tuple[int, int]],
    mask: np.ndarray,
) -> List[Tuple[int, int]]:
    """沿端点局部方向延伸到可见轮廓，避免骨架像素内缩造成系统性偏短。"""
    if len(path) < 2:
        return path
    window = min(6, max(1, len(path) // 3))
    start_direction = np.array(
        [path[0][0] - path[window][0], path[0][1] - path[window][1]], dtype=np.float64
    )
    end_direction = np.array(
        [path[-1][0] - path[-window - 1][0], path[-1][1] - path[-window - 1][1]], dtype=np.float64
    )
    start_extra = _extend_one_endpoint(path[0], start_direction, mask)
    end_extra = _extend_one_endpoint(path[-1], end_direction, mask)
    return list(reversed(start_extra)) + path + end_extra


def _extend_one_endpoint(
    endpoint: Tuple[int, int],
    direction: np.ndarray,
    mask: np.ndarray,
) -> List[Tuple[int, int]]:
    norm = float(np.linalg.norm(direction))
    if norm <= 1e-6:
        return []
    direction = direction / norm
    rows, cols = mask.shape
    extra: List[Tuple[int, int]] = []
    last = endpoint
    # 2 倍主体厚度足以覆盖骨架中心到轮廓的可见距离，超过边界立即停止。
    for step in range(1, 80):
        row = int(round(endpoint[0] + direction[0] * step))
        col = int(round(endpoint[1] + direction[1] * step))
        if row < 0 or row >= rows or col < 0 or col >= cols or mask[row, col] == 0:
            break
        point = (row, col)
        if point != last:
            extra.append(point)
            last = point
    return extra


def _bfs_shortest_path(
    pixel_set: set[Tuple[int, int]],
    start: Tuple[int, int],
    goal: Tuple[int, int],
) -> Optional[List[Tuple[int, int]]]:
    from collections import deque

    queue = deque([start])
    parent: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {start: None}
    while queue:
        current = queue.popleft()
        if current == goal:
            path: List[Tuple[int, int]] = []
            node: Optional[Tuple[int, int]] = goal
            while node is not None:
                path.append(node)
                node = parent[node]
            return list(reversed(path))
        for neighbor in _neighbors(*current, pixel_set):
            if neighbor not in parent:
                parent[neighbor] = current
                queue.append(neighbor)
    return None


def _polyline_length_8connected(path: Sequence[Tuple[int, int]]) -> float:
    return float(
        sum(
            math.hypot(path[index][0] - path[index + 1][0], path[index][1] - path[index + 1][1])
            for index in range(len(path) - 1)
        )
    )


def _geometry_confidence(
    *,
    is_measurable: bool,
    solidity: float,
    axis_stability: float,
    path_score: float,
    path_score_gap: float,
    main_path_ratio: float,
    hole_area_ratio: float,
    secondary_ratio: float,
) -> float:
    value = (
        0.25 * np.clip(solidity, 0.0, 1.0)
        + 0.20 * np.clip(axis_stability / 5.0, 0.0, 1.0)
        + 0.25 * np.clip(path_score, 0.0, 1.0)
        + 0.15 * np.clip(path_score_gap / 0.25, 0.0, 1.0)
        + 0.10 * np.clip(main_path_ratio, 0.0, 1.0)
        + 0.05 * max(0.0, 1.0 - hole_area_ratio - secondary_ratio)
    )
    return float(np.clip(value if is_measurable else value * 0.45, 0.0, 1.0))


def _unique_reasons(reasons: Iterable[str]) -> List[str]:
    return list(dict.fromkeys(reasons))
