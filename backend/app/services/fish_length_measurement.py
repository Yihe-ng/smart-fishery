"""Fish body length measurement via PCA main axis and skeleton centerline arc.

Replaces simple minAreaRect with geometry-aware measurement that adapts to
straight vs curved fish and gates out unmeasurable instances.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import cv2
import numpy as np
from skimage.morphology import skeletonize


# ---------------------------------------------------------------------------
# Tunable constants (initial values per the measurement plan; to be calibrated)
# ---------------------------------------------------------------------------
MIN_AREA_PX = 60           # discard masks smaller than this
MIN_SOLIDITY = 0.60        # below this → low confidence or unmeasurable
MIN_MAIN_PATH_RATIO = 0.65 # below this → unmeasurable
CURVATURE_THRESHOLD_STRAIGHT = 1.05  # below → use PCA main axis
CURVATURE_THRESHOLD_BENT = 1.25      # above → low confidence
BRANCH_COUNT_MAX = 12      # skeleton branch-point count upper bound
ENDPOINT_COUNT_MAX = 6     # skeleton endpoint count upper bound (fins add endpoints)


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------
@dataclass
class MeasurementResult:
    primary_length_px: float = 0.0
    visible_mask_length_px: float = 0.0
    measurement_method: str = "none"       # pca_main_axis | centerline_arc | fallback_minrect
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


# ---------------------------------------------------------------------------
# Public entry-point
# ---------------------------------------------------------------------------
def measure_fish_length(
    polygon_px: np.ndarray,
    image_width: int,
    image_height: int,
) -> MeasurementResult:
    """Compute primary body length for a single fish instance.

    Parameters
    ----------
    polygon_px : np.ndarray
        Mask polygon in pixel coordinates, shape (N, 2), dtype float32.
    image_width, image_height : int
        Original image dimensions (for border-touch detection).

    Returns
    -------
    MeasurementResult
    """

    # -- 1. Guard: degenerate input ----------------------------------------
    if len(polygon_px) < 5:
        return MeasurementResult(reasons=["polygon_too_few_points"])

    # -- 2. Rasterise polygon to binary mask --------------------------------
    mask = _polygon_to_mask(polygon_px, image_width, image_height)
    area = int(cv2.countNonZero(mask))
    if area < MIN_AREA_PX:
        return MeasurementResult(area=area, reasons=["area_too_small"], is_measurable=False)

    # -- 3. Contour & measurability gating ---------------------------------
    contour, hull = _extract_largest_contour(mask)
    if contour is None:
        return MeasurementResult(area=area, reasons=["contour_extraction_failed"], is_measurable=False)

    solidity = _compute_solidity(contour, hull)
    touch_border = _touches_image_border(mask)

    if touch_border:
        # border-touch → low-confidence, but still attempt measurement
        pass

    # -- 4. PCA main axis --------------------------------------------------
    pca_length, main_axis_vec = _pca_projection_length(contour)
    if pca_length is None or pca_length <= 0:
        # fallback to minAreaRect
        pca_length = _min_rect_length(contour)
        main_axis_vec = None
    main_axis_length = pca_length

    # -- 5. Skeleton & centerline ------------------------------------------
    centerline_length, skeleton_info = _compute_centerline(mask)
    endpoint_count = skeleton_info.get("endpoints", 0)
    branch_count = skeleton_info.get("branches", 0)
    main_path_ratio = skeleton_info.get("main_path_ratio", 1.0)

    # -- 6. Curvature decision ---------------------------------------------
    if centerline_length is not None and main_axis_length > 0:
        curvature_ratio = centerline_length / main_axis_length
        straightness_ratio = main_axis_length / centerline_length
    else:
        curvature_ratio = 1.0
        straightness_ratio = 1.0

    # Choose measurement method & primary length
    if curvature_ratio < CURVATURE_THRESHOLD_STRAIGHT:
        primary_length = main_axis_length
        measurement_method = "pca_main_axis"
    elif curvature_ratio < CURVATURE_THRESHOLD_BENT and centerline_length is not None:
        primary_length = centerline_length
        measurement_method = "centerline_arc"
    elif centerline_length is not None:
        # Severely bent → use centerline but flag low confidence
        primary_length = centerline_length
        measurement_method = "centerline_arc"
    else:
        primary_length = main_axis_length
        measurement_method = "pca_main_axis"

    # -- 7. Measurability rules --------------------------------------------
    reasons: List[str] = []
    is_measurable = True

    if touch_border:
        reasons.append("touch_border")
        is_measurable = False
    if solidity < MIN_SOLIDITY:
        reasons.append(f"low_solidity({solidity:.2f})")
        is_measurable = False
    if main_path_ratio < MIN_MAIN_PATH_RATIO:
        reasons.append(f"low_main_path_ratio({main_path_ratio:.2f})")
        is_measurable = False
    if endpoint_count > ENDPOINT_COUNT_MAX:
        reasons.append(f"too_many_endpoints({endpoint_count})")
        is_measurable = False
    if branch_count > BRANCH_COUNT_MAX:
        reasons.append(f"too_many_branches({branch_count})")
        is_measurable = False
    if curvature_ratio >= CURVATURE_THRESHOLD_BENT:
        reasons.append(f"severely_bent({curvature_ratio:.2f})")
        is_measurable = False

    return MeasurementResult(
        primary_length_px=primary_length,
        visible_mask_length_px=centerline_length or main_axis_length,
        measurement_method=measurement_method,
        is_measurable=is_measurable,
        reasons=reasons,
        curvature_ratio=round(curvature_ratio, 4),
        straightness_ratio=round(straightness_ratio, 4),
        main_axis_length_px=main_axis_length,
        centerline_length_px=centerline_length or 0.0,
        area=area,
        solidity=round(solidity, 4),
        touch_border=touch_border,
        endpoint_count=endpoint_count,
        branch_count=branch_count,
        main_path_ratio=round(main_path_ratio, 4),
    )


# ===================================================================
# Internal helpers
# ===================================================================

def _polygon_to_mask(
    polygon_px: np.ndarray, image_width: int, image_height: int
) -> np.ndarray:
    """Rasterise a polygon to a binary mask (uint8, 0/255)."""
    mask = np.zeros((image_height, image_width), dtype=np.uint8)
    pts = polygon_px.reshape(-1, 1, 2).astype(np.int32)
    cv2.fillPoly(mask, [pts], 255)
    return mask


def _extract_largest_contour(
    mask: np.ndarray,
) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    """Return the largest contour and its convex hull from a binary mask."""
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None, None
    largest = max(contours, key=cv2.contourArea)
    hull = cv2.convexHull(largest)
    return largest, hull


def _compute_solidity(contour: np.ndarray, hull: np.ndarray) -> float:
    """solidity = contour_area / convex_hull_area."""
    contour_area = float(cv2.contourArea(contour))
    hull_area = float(cv2.contourArea(hull))
    if hull_area <= 0:
        return 1.0
    return contour_area / hull_area


def _touches_image_border(mask: np.ndarray, margin: int = 1) -> bool:
    """Check whether the mask touches the image border.

    Only the outermost *margin* rows/columns are checked.  margin=1 catches
    fish whose mask literally reaches the image boundary (partially out of frame).
    """
    h, w = mask.shape
    if h <= margin * 2 or w <= margin * 2:
        return True
    if mask[:margin, :].any() or mask[-margin:, :].any():
        return True
    if mask[:, :margin].any() or mask[:, -margin:].any():
        return True
    return False


def _pca_projection_length(
    contour: np.ndarray,
) -> Tuple[Optional[float], Optional[np.ndarray]]:
    """Compute the projection span of contour points onto the first principal axis."""
    pts = contour.reshape(-1, 2).astype(np.float32)
    if len(pts) < 3:
        return None, None

    mean = pts.mean(axis=0)
    centered = pts - mean
    # SVD is more numerically stable than eigendecomposition on the covariance matrix
    try:
        u, s, vt = np.linalg.svd(centered, full_matrices=False)
    except np.linalg.LinAlgError:
        return None, None

    main_axis = vt[0]  # first principal component (unit vector)
    projections = centered @ main_axis
    length = float(projections.max() - projections.min())
    return length, main_axis


def _min_rect_length(contour: np.ndarray) -> float:
    """Fallback: length = longer side of minimum-area rotated rectangle."""
    if len(contour) < 5:
        return 0.0
    rect = cv2.minAreaRect(contour.astype(np.float32))
    w, h = rect[1]
    return float(max(w, h))


def _compute_centerline(mask: np.ndarray) -> Tuple[Optional[float], dict]:
    """Skeletonise the binary mask and return the centerline arc length + diagnostic info.

    Returns
    -------
    length : float | None
        Arc length in pixels, or None if skeletonisation failed.
    info : dict
        Keys: endpoints, branches, main_path_ratio.
    """
    info: dict = {"endpoints": 0, "branches": 0, "main_path_ratio": 1.0}
    try:
        binary = (mask > 0).astype(np.uint8)
        skeleton = skeletonize(binary)
    except Exception:
        return None, info

    if not skeleton.any():
        return None, info

    # Gather all skeleton pixels as (row, col)
    skeleton_pixels = np.column_stack(np.where(skeleton))
    if len(skeleton_pixels) < 2:
        return None, info

    pixel_set: set = {tuple(p) for p in skeleton_pixels}

    # Classify each pixel as endpoint (1 neighbour), junction (≥3), or path (2)
    endpoints: List[Tuple[int, int]] = []
    branch_pts: List[Tuple[int, int]] = []
    for r, c in skeleton_pixels:
        n = _count_8_neighbors(r, c, pixel_set)
        if n == 1:
            endpoints.append((int(r), int(c)))
        elif n >= 3:
            branch_pts.append((int(r), int(c)))

    # Compute true total skeleton arc length by summing edges exactly once.
    # For each pixel, only count edges to "forward" neighbours (raster-scan order)
    # to avoid double-counting.
    total_length = 0.0
    for r, c in skeleton_pixels:
        for dr, dc in [(0, 1), (1, 0), (1, 1), (1, -1)]:
            if (r + dr, c + dc) in pixel_set:
                total_length += math.sqrt(dr * dr + dc * dc)

    info["endpoints"] = len(endpoints)
    info["branches"] = len(branch_pts)
    # Store total skeleton length as base for main_path_ratio
    info["total_skeleton_length"] = total_length

    if len(endpoints) < 2:
        info["main_path_ratio"] = 0.0  # skeleton degraded → definitely unmeasurable
        return None, info

    # Find the two farthest endpoints
    best_pair = _farthest_pair(endpoints)
    if best_pair is None:
        return None, info

    # BFS shortest path between the two farthest endpoints
    path = _bfs_shortest_path(pixel_set, *best_pair)
    if path is None or len(path) < 2:
        return None, info

    candidate_arc = _polyline_length_8connected(path)
    if candidate_arc <= 0:
        return None, info

    # -- Prune short branches (plan §第一版骨架主路径剪枝策略) --
    main_path_set = set(path)
    pruned_set = _prune_short_branches(pixel_set, branch_pts, main_path_set, candidate_arc)
    if len(pruned_set) < len(pixel_set):
        # Re-classify after pruning
        pixel_set = pruned_set
        endpoints.clear()
        branch_pts.clear()
        for r, c in pixel_set:
            n = _count_8_neighbors(r, c, pixel_set)
            if n == 1:
                endpoints.append((int(r), int(c)))
            elif n >= 3:
                branch_pts.append((int(r), int(c)))
        info["endpoints"] = len(endpoints)
        info["branches"] = len(branch_pts)

        # Re-run farthest-pair + BFS on pruned skeleton
        best_pair = _farthest_pair(endpoints)
        if best_pair is None:
            return None, info
        path = _bfs_shortest_path(pixel_set, *best_pair)
        if path is None or len(path) < 2:
            return None, info

    arc_length = _polyline_length_8connected(path)
    if arc_length <= 0:
        return None, info

    info["main_path_ratio"] = min(1.0, arc_length / max(total_length, 1.0))
    return arc_length, info


def _count_8_neighbors(r: int, c: int, pixel_set: set) -> int:
    """Number of 8-connected skeleton neighbours."""
    count = 0
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            if (r + dr, c + dc) in pixel_set:
                count += 1
    return count


def _farthest_pair(
    points: List[Tuple[int, int]],
) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
    """Return the two points with the largest Euclidean distance."""
    if len(points) < 2:
        return None
    max_d = -1.0
    best = (points[0], points[1])
    for i, a in enumerate(points):
        for b in points[i + 1 :]:
            d = (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2
            if d > max_d:
                max_d = d
                best = (a, b)
    return best


def _bfs_shortest_path(
    pixel_set: set,
    start: Tuple[int, int],
    goal: Tuple[int, int],
) -> Optional[List[Tuple[int, int]]]:
    """BFS over the 8-connected skeleton graph, returning the shortest pixel path."""
    from collections import deque

    if start not in pixel_set or goal not in pixel_set:
        return None

    queue: deque = deque([start])
    parent: dict = {start: None}
    visited = {start}

    while queue:
        current = queue.popleft()
        if current == goal:
            break
        r, c = current
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                neighbor = (r + dr, c + dc)
                if neighbor in pixel_set and neighbor not in visited:
                    visited.add(neighbor)
                    parent[neighbor] = current
                    queue.append(neighbor)
    else:
        # goal unreachable
        return None

    # Reconstruct path
    path: List[Tuple[int, int]] = []
    node = goal
    while node is not None:
        path.append(node)
        node = parent[node]
    path.reverse()
    return path


def _polyline_length_8connected(path: List[Tuple[int, int]]) -> float:
    """Sum of Euclidean distances between consecutive 8-connected pixels."""
    total = 0.0
    for i in range(len(path) - 1):
        dr = path[i][0] - path[i + 1][0]
        dc = path[i][1] - path[i + 1][1]
        # diagonal step = sqrt(2), axial step = 1
        total += math.sqrt(dr * dr + dc * dc)
    return total


def _prune_short_branches(
    pixel_set: set,
    branch_pts: List[Tuple[int, int]],
    main_path_set: set,
    candidate_length: float,
    prune_ratio: float = 0.05,
) -> set:
    """Remove branches shorter than prune_ratio * candidate_length.

    Per the measurement plan: delete branch pixels whose total length is
    less than 5–10% of the main-path candidate length, then re-classify
    endpoints/branches for a cleaner main-path search.
    """
    pruned: set = set()
    for bp in branch_pts:
        if bp not in pixel_set:
            continue
        r, c = bp
        for dr, dc in [
            (0, 1), (1, 0), (0, -1), (-1, 0),
            (1, 1), (1, -1), (-1, 1), (-1, -1),
        ]:
            neighbor = (r + dr, c + dc)
            if neighbor not in pixel_set or neighbor in main_path_set:
                continue
            branch = _trace_branch(neighbor, bp, pixel_set, main_path_set)
            branch_length = _polyline_length_8connected(branch)
            if branch_length < prune_ratio * candidate_length:
                pruned.update(branch)
    return pixel_set - pruned


def _trace_branch(
    start: Tuple[int, int],
    parent: Tuple[int, int],
    pixel_set: set,
    main_path_set: set,
) -> List[Tuple[int, int]]:
    """Trace a branch outward from *start* until an endpoint or junction."""
    path: List[Tuple[int, int]] = [start]
    current = start
    prev = parent
    while True:
        r, c = current
        neighbors = []
        for dr, dc in [
            (0, 1), (1, 0), (0, -1), (-1, 0),
            (1, 1), (1, -1), (-1, 1), (-1, -1),
        ]:
            nb = (r + dr, c + dc)
            if nb != prev and nb in pixel_set:
                neighbors.append(nb)
        if len(neighbors) == 1:
            # Continue along the branch
            path.append(neighbors[0])
            prev = current
            current = neighbors[0]
        else:
            # Endpoint (0 neighbors) or junction (≥2 neighbors) — stop
            break
    return path
