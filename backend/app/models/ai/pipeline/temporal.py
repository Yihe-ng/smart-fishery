"""TemporalProcessor：可插拔因果时序策略（S1/S2 移植自 model_training V12）。

来源：model_training V12 frozen_config + scripts/v12_common.py（冻结常数，
不调参）。实现原则：
- 图片模式永远 disabled；
- 视频模式由 manifest 决定，默认 disabled（V12 最终部署选择尚未冻结）；
- 因果：只用 t-2 / t-1 历史帧，禁止未来帧；
- 统一 fallback：历史缺失/被拒/歧义 -> 当前单帧概率，绝不丢鱼；
- 状态按 stream_id 隔离，支持 reset / clear_expired（TTL）。
"""

from __future__ import annotations

import math
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, List, Optional, Tuple

import numpy as np

from app.models.ai.pipeline.contracts import (
    FishInstance,
    TemporalOutcome,
    TemporalPolicyProtocol,
)


# ---------------------------------------------------------------------------
# 冻结关联常数（V12 frozen_config / v12_common.py，禁止随意改动）
# ---------------------------------------------------------------------------

A0_IOU_THRESHOLD = 0.25

A1_SCORE_WEIGHTS = {
    "mask_iou": 0.45,
    "bbox_iou": 0.25,
    "centroid": 0.20,
    "area_ratio": 0.10,
}

A1_GATES = {
    "mask_iou_min": 0.25,
    "centroid_distance_norm_max": 0.75,
    "area_ratio_min": 0.5,
    "area_ratio_max": 2.0,
    "composite_score_min": 0.45,
    "best_minus_second_best_min": 0.10,
    "mutual_best": True,
}

DEFAULT_MAX_FRAME_GAP = 10
DEFAULT_WINDOW = 3
DEFAULT_TTL_SECONDS = 60 * 60  # 与视频任务 TTL 对齐


# ---------------------------------------------------------------------------
# 关联几何工具（逐项移植 v12_common.py）
# ---------------------------------------------------------------------------


def mask_iou(left: np.ndarray, right: np.ndarray) -> float:
    """mask IoU，stride 降采样与参考一致（最长边超过 512 时降采样）。"""
    stride = max(1, int(np.ceil(max(left.shape) / 512)))
    a = left[::stride, ::stride]
    b = right[::stride, ::stride]
    union = int(np.logical_or(a, b).sum())
    if not union:
        return 0.0
    return float(np.logical_and(a, b).sum() / union)


def bbox_iou(
    left: tuple[float, float, float, float],
    right: tuple[float, float, float, float],
) -> float:
    """bbox IoU（xyxy，像素）。"""
    lx0, ly0, lx1, ly1 = left
    rx0, ry0, rx1, ry1 = right
    ix0, iy0 = max(lx0, rx0), max(ly0, ry0)
    ix1, iy1 = min(lx1, rx1), min(ly1, ry1)
    inter = max(0.0, ix1 - ix0) * max(0.0, iy1 - iy0)
    la = max(0.0, lx1 - lx0) * max(0.0, ly1 - ly0)
    ra = max(0.0, rx1 - rx0) * max(0.0, ry1 - ry0)
    union = la + ra - inter
    return inter / union if union > 0.0 else 0.0


def bbox_xyxy(mask: np.ndarray) -> tuple[float, float, float, float]:
    """bool mask 的 tight bbox（exclusive xyxy）。"""
    ys, xs = np.where(mask)
    if not len(xs):
        raise ValueError("empty mask")
    return (
        float(xs.min()),
        float(ys.min()),
        float(xs.max()) + 1.0,
        float(ys.max()) + 1.0,
    )


def centroid(bbox: tuple[float, float, float, float]) -> tuple[float, float]:
    return (bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0


def mask_geometry(mask: np.ndarray) -> dict[str, Any]:
    """实例描述符：mask + bbox + centroid + area（与 v12_common 一致）。"""
    bbox = bbox_xyxy(mask)
    cx, cy = centroid(bbox)
    return {
        "mask": mask,
        "bbox": bbox,
        "centroid": (cx, cy),
        "area": float(mask.sum()),
    }


def composite_score(
    left: dict[str, Any],
    right: dict[str, Any],
    image_diag: float,
) -> dict[str, float]:
    """A1 复合得分（预注册权重，禁止调参）。"""
    m_iou = mask_iou(left["mask"], right["mask"])
    b_iou = bbox_iou(left["bbox"], right["bbox"])
    lcx, lcy = left["centroid"]
    rcx, rcy = right["centroid"]
    centroid_norm = float(np.hypot(lcx - rcx, lcy - rcy) / max(image_diag, 1e-9))
    area_ratio = (
        float(left["area"] / right["area"]) if right["area"] > 0 else float("inf")
    )
    score = (
        A1_SCORE_WEIGHTS["mask_iou"] * m_iou
        + A1_SCORE_WEIGHTS["bbox_iou"] * b_iou
        + A1_SCORE_WEIGHTS["centroid"] * math.exp(-centroid_norm)
        + A1_SCORE_WEIGHTS["area_ratio"] * math.exp(-abs(math.log(area_ratio)))
    )
    return {
        "mask_iou": m_iou,
        "bbox_iou": b_iou,
        "centroid_norm": centroid_norm,
        "area_ratio": area_ratio,
        "composite": float(score),
    }


def mutual_best_a0(
    current: list[dict[str, Any]],
    history: list[dict[str, Any]],
) -> dict[int, tuple[int, float]]:
    """A0 冻结参考：mutual-best mask-IoU 一一确认。"""
    best_left: dict[int, tuple[int, float]] = {}
    best_right: dict[int, tuple[int, float]] = {}
    for ci, cur in enumerate(current):
        for hi, his in enumerate(history):
            iou = mask_iou(cur["mask"], his["mask"])
            if iou < A0_IOU_THRESHOLD:
                continue
            if ci not in best_left or iou > best_left[ci][1]:
                best_left[ci] = (hi, iou)
            if hi not in best_right or iou > best_right[hi][1]:
                best_right[hi] = (ci, iou)
    confirmed: dict[int, tuple[int, float]] = {}
    for ci, (hi, iou) in best_left.items():
        reverse = best_right.get(hi)
        if reverse is not None and reverse[0] == ci:
            confirmed[ci] = (hi, iou)
    return confirmed


def _a1_link_scores(
    current: list[dict[str, Any]],
    history: list[dict[str, Any]],
    image_diag: float,
) -> list[dict[str, Any]]:
    """逐对 A1 得分，先按 mask IoU >= 0.25 预过滤。"""
    rows: list[dict[str, Any]] = []
    for ci, cur in enumerate(current):
        for hi, his in enumerate(history):
            parts = composite_score(cur, his, image_diag)
            if parts["mask_iou"] < A1_GATES["mask_iou_min"]:
                continue
            rows.append({"ci": ci, "hi": hi, **parts})
    return rows


def a1_gated_hungarian(
    current: list[dict[str, Any]],
    history: list[dict[str, Any]],
    image_diag: float,
) -> tuple[dict[int, dict[str, Any]], dict[str, Any]]:
    """A1：precision-first gated Hungarian（逐项移植 v12_common）。

    Returns
    -------
    (accepted, stats)
      accepted : {current_index: link_detail}
    """
    from collections import defaultdict

    from scipy.optimize import linear_sum_assignment

    scores = _a1_link_scores(current, history, image_diag)
    best_by_ci: dict[int, list[dict[str, Any]]] = defaultdict(list)
    best_by_hi: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in scores:
        best_by_ci[row["ci"]].append(row)
        best_by_hi[row["hi"]].append(row)
    for mapping in (best_by_ci, best_by_hi):
        for key, rows in mapping.items():
            rows.sort(key=lambda item: item["composite"], reverse=True)

    n_cur = len(current)
    n_hist = len(history)
    accepted: dict[int, dict[str, Any]] = {}
    stats: dict[str, Any] = {
        "current_instances": n_cur,
        "history_instances": n_hist,
        "candidate_pairs_after_mask_iou_filter": len(scores),
        "matched_pairs": 0,
        "unmatched_current": n_cur,
        "accepted_links": 0,
        "rejected_gate": 0,
        "rejected_ambiguous": 0,
    }
    if not scores or n_cur == 0 or n_hist == 0:
        return accepted, stats

    cost = np.zeros((n_cur, n_hist), dtype=np.float64)
    score_lookup: dict[tuple[int, int], dict[str, Any]] = {}
    for row in scores:
        cost[row["ci"], row["hi"]] = row["composite"]
        score_lookup[(row["ci"], row["hi"])] = row

    row_idx, col_idx = linear_sum_assignment(-cost)
    matched_positive = 0
    matched: list[tuple[int, int, float]] = []
    for ci, hi in zip(row_idx, col_idx):
        value = float(cost[ci, hi])
        if value > 0.0:
            matched_positive += 1
        matched.append((int(ci), int(hi), value))
    stats["matched_pairs"] = matched_positive
    stats["unmatched_current"] = n_cur - matched_positive
    matched.sort(key=lambda item: item[2], reverse=True)

    for ci, hi, match_score in matched:
        if match_score <= 0.0:
            continue
        detail = dict(score_lookup.get((ci, hi), {}))
        if not detail:
            continue
        if (
            detail["composite"] < A1_GATES["composite_score_min"]
            or detail["centroid_norm"] > A1_GATES["centroid_distance_norm_max"]
            or detail["area_ratio"] < A1_GATES["area_ratio_min"]
            or detail["area_ratio"] > A1_GATES["area_ratio_max"]
        ):
            stats["rejected_gate"] += 1
            continue
        cur_rows = best_by_ci.get(ci, [])
        his_rows = best_by_hi.get(hi, [])
        cur_margin = (
            cur_rows[0]["composite"] - cur_rows[1]["composite"]
            if len(cur_rows) >= 2
            else cur_rows[0]["composite"]
        )
        his_margin = (
            his_rows[0]["composite"] - his_rows[1]["composite"]
            if len(his_rows) >= 2
            else his_rows[0]["composite"]
        )
        if (
            cur_margin < A1_GATES["best_minus_second_best_min"]
            or his_margin < A1_GATES["best_minus_second_best_min"]
        ):
            stats["rejected_gate"] += 1
            continue
        cur_best_hi = cur_rows[0]["hi"] if cur_rows else None
        his_best_ci = his_rows[0]["ci"] if his_rows else None
        if cur_best_hi != hi or his_best_ci != ci:
            stats["rejected_ambiguous"] += 1
            continue
        accepted[ci] = {
            "history_index": hi,
            "mask_iou": detail["mask_iou"],
            "bbox_iou": detail["bbox_iou"],
            "centroid_norm": detail["centroid_norm"],
            "area_ratio": detail["area_ratio"],
            "composite": detail["composite"],
            "cur_margin": float(cur_margin),
            "his_margin": float(his_margin),
        }
        stats["accepted_links"] += 1

    if len(accepted) != len({int(ci) for ci in accepted}):
        raise RuntimeError("A1 accepted links violate current-instance uniqueness")
    history_indices = [int(detail["history_index"]) for detail in accepted.values()]
    if len(history_indices) != len(set(history_indices)):
        raise RuntimeError("A1 accepted links violate history-instance uniqueness")
    return accepted, stats


# ---------------------------------------------------------------------------
# 时序状态存储（stream_id 隔离 + TTL）
# ---------------------------------------------------------------------------


@dataclass
class InstanceState:
    instance_id: str
    geometry: dict[str, Any]  # mask/bbox/centroid/area（v12 mask_geometry 结构）
    probability: float  # 该帧单帧 P(measurable)


@dataclass
class FrameState:
    frame_index: int
    timestamp_sec: Optional[float]
    entries: List[InstanceState] = field(default_factory=list)


@dataclass
class StreamState:
    stream_id: str
    frames: Deque[FrameState] = field(default_factory=deque)
    last_seen_sec: float = 0.0


class TemporalStateStore:
    """按 stream_id 隔离的时序历史（窗口裁剪 + TTL 清理）。"""

    def __init__(
        self,
        *,
        window: int = DEFAULT_WINDOW,
        ttl_seconds: float = DEFAULT_TTL_SECONDS,
        now_fn: Optional[Any] = None,
    ):
        self._window = max(1, window)
        self._ttl_seconds = float(ttl_seconds)
        self._now_fn = now_fn or time.time
        self._streams: Dict[str, StreamState] = {}
        self._lock = threading.Lock()

    def _now(self) -> float:
        return float(self._now_fn())

    def reset(self, stream_id: str) -> None:
        with self._lock:
            self._streams.pop(stream_id, None)

    def clear_expired(self, now: Optional[float] = None) -> int:
        """清理超过 TTL 的 stream 状态，返回清理数量。"""
        current = float(now) if now is not None else self._now()
        with self._lock:
            expired = [
                stream_id
                for stream_id, state in self._streams.items()
                if current - state.last_seen_sec > self._ttl_seconds
            ]
            for stream_id in expired:
                del self._streams[stream_id]
            return len(expired)

    def clear_all(self) -> int:
        with self._lock:
            count = len(self._streams)
            self._streams.clear()
            return count

    def stream_count(self) -> int:
        with self._lock:
            return len(self._streams)

    def push_frame(
        self,
        stream_id: str,
        *,
        frame_index: int,
        timestamp_sec: Optional[float],
        entries: List[InstanceState],
    ) -> None:
        """写入当前帧状态（内部裁剪到 window 帧并更新时间戳）。"""
        with self._lock:
            state = self._streams.get(stream_id)
            if state is None:
                state = StreamState(stream_id=stream_id)
                self._streams[stream_id] = state
            state.frames.append(
                FrameState(
                    frame_index=frame_index,
                    timestamp_sec=timestamp_sec,
                    entries=list(entries),
                )
            )
            while len(state.frames) > self._window:
                state.frames.popleft()
            state.last_seen_sec = self._now()

    def nearest_past_frame(
        self, stream_id: str, current_frame_index: int
    ) -> Optional[FrameState]:
        """返回当前帧之前最近的历史帧（frame_index 差值最小且 < 当前帧）。"""
        with self._lock:
            state = self._streams.get(stream_id)
            if state is None:
                return None
            candidates = [
                frame
                for frame in state.frames
                if frame.frame_index < current_frame_index
            ]
            if not candidates:
                return None
            return max(candidates, key=lambda frame: frame.frame_index)

    def snapshot(self, stream_id: str) -> List[FrameState]:
        """测试辅助：返回 stream 当前帧状态拷贝。"""
        with self._lock:
            state = self._streams.get(stream_id)
            if state is None:
                return []
            return [FrameState(frame_index=f.frame_index, timestamp_sec=f.timestamp_sec, entries=list(f.entries)) for f in state.frames]


# ---------------------------------------------------------------------------
# 策略实现
# ---------------------------------------------------------------------------


class DisabledTemporalPolicy(TemporalPolicyProtocol):
    """disabled：无状态，永远返回单帧概率（图片模式强制使用）。"""

    name = "disabled"

    def reset(self, stream_id: str) -> None:
        return None

    def clear_expired(self, now: Optional[float] = None) -> int:
        return 0

    def apply(
        self,
        stream_id: str,
        frame_meta: dict[str, Any],
        instances: List[FishInstance],
        probabilities: List[float],
    ) -> List[TemporalOutcome]:
        return [
            TemporalOutcome(
                instance_id=instance.instance_id,
                single_probability=float(probability),
                final_probability=float(probability),
                applied=False,
                policy=self.name,
                fallback_reason="disabled",
                history_count=0,
            )
            for instance, probability in zip(instances, probabilities)
        ]

    def update(
        self,
        stream_id: str,
        frame_meta: dict[str, Any],
        instances: List[FishInstance],
        probabilities: List[float],
    ) -> None:
        return None


class _CausalMeanPolicyBase(TemporalPolicyProtocol):
    """因果历史概率均值 + 单帧 fallback 的公共逻辑。

    子类实现 _associate(current_geoms, history_geoms, image_diag)，
    返回 {current_index: history_index}（A0/A1 分别实现）。
    """

    name = "base"
    _reason_no_history = "no_history"
    _reason_link_missing = "link_missing"
    _reason_history_ineligible = "history_ineligible"

    def __init__(
        self,
        *,
        window: int = DEFAULT_WINDOW,
        max_frame_gap: int = DEFAULT_MAX_FRAME_GAP,
        ttl_seconds: float = DEFAULT_TTL_SECONDS,
        now_fn: Optional[Any] = None,
        store: Optional[TemporalStateStore] = None,
    ):
        self._max_frame_gap = max_frame_gap
        self._store = store or TemporalStateStore(
            window=window, ttl_seconds=ttl_seconds, now_fn=now_fn
        )

    def reset(self, stream_id: str) -> None:
        self._store.reset(stream_id)

    def clear_expired(self, now: Optional[float] = None) -> int:
        return self._store.clear_expired(now)

    def _associate(
        self,
        current_geoms: list[dict[str, Any]],
        history_geoms: list[dict[str, Any]],
        image_diag: float,
    ) -> dict[int, int]:
        raise NotImplementedError

    def apply(
        self,
        stream_id: str,
        frame_meta: dict[str, Any],
        instances: List[FishInstance],
        probabilities: List[float],
    ) -> List[TemporalOutcome]:
        frame_index = int(frame_meta.get("frame_index", 0))
        image_diag = float(frame_meta.get("image_diag") or 1.0)
        current_geoms = [
            mask_geometry(instance.mask) for instance in instances
        ]

        t1 = self._store.nearest_past_frame(stream_id, frame_index)
        t2: Optional[FrameState] = None
        if t1 is not None and (frame_index - t1.frame_index) <= self._max_frame_gap:
            t2 = self._store.nearest_past_frame(stream_id, t1.frame_index)
            if t2 is not None and (t1.frame_index - t2.frame_index) > self._max_frame_gap:
                t2 = None
        else:
            t1 = None

        link1: Optional[dict[int, int]] = None  # current -> t1
        link2: Optional[dict[int, int]] = None  # t1 -> t2
        t1_geoms = [entry.geometry for entry in t1.entries] if t1 else []
        t2_geoms = [entry.geometry for entry in t2.entries] if t2 else []

        if t1 is not None and t1.entries:
            link1 = self._associate(current_geoms, t1_geoms, image_diag)
            if t2 is not None and t2.entries:
                link2 = self._associate(t1_geoms, t2_geoms, image_diag)

        outcomes: List[TemporalOutcome] = []
        for index, (instance, probability) in enumerate(zip(instances, probabilities)):
            single = float(probability)
            history_probs: List[float] = []
            reason: Optional[str] = None
            if t1 is None:
                reason = self._reason_no_history
            elif link1 is None or index not in link1:
                reason = self._reason_link_missing
            else:
                t1_index = link1[index]
                if t1_index < len(t1.entries):
                    history_probs.append(t1.entries[t1_index].probability)
                    if link2 is not None and t1_index in link2:
                        t2_index = link2[t1_index]
                        if t2_index < len(t2.entries):
                            history_probs.append(t2.entries[t2_index].probability)
                if not history_probs:
                    reason = self._reason_history_ineligible

            if history_probs:
                final_probability = float(np.mean([single, *history_probs]))
                applied = True
            else:
                final_probability = single
                applied = False
            outcomes.append(
                TemporalOutcome(
                    instance_id=instance.instance_id,
                    single_probability=single,
                    final_probability=final_probability,
                    applied=applied,
                    policy=self.name,
                    fallback_reason=reason,
                    history_count=len(history_probs),
                )
            )
        return outcomes

    def update(
        self,
        stream_id: str,
        frame_meta: dict[str, Any],
        instances: List[FishInstance],
        probabilities: List[float],
    ) -> None:
        """当前帧推理完成后写入历史（因果：当前帧不用于自身平滑）。"""
        entries = [
            InstanceState(
                instance_id=instance.instance_id,
                geometry=mask_geometry(instance.mask),
                probability=float(probability),
            )
            for instance, probability in zip(instances, probabilities)
        ]
        self._store.push_frame(
            stream_id,
            frame_index=int(frame_meta.get("frame_index", 0)),
            timestamp_sec=frame_meta.get("timestamp_sec"),
            entries=entries,
        )


class CausalMeanPolicy(_CausalMeanPolicyBase):
    """S1：A0 mutual-best mask-IoU 关联 + 因果概率均值。"""

    name = "causal_mean"

    def _associate(
        self,
        current_geoms: list[dict[str, Any]],
        history_geoms: list[dict[str, Any]],
        image_diag: float,
    ) -> dict[int, int]:
        confirmed = mutual_best_a0(current_geoms, history_geoms)
        return {current_index: history_index for current_index, (history_index, _) in confirmed.items()}


class GatedCausalPolicy(_CausalMeanPolicyBase):
    """S2：A1 gated Hungarian 关联 + 因果概率均值（V12 STRONG PASS 方案）。"""

    name = "gated_causal"
    _reason_gate_rejected = "gate_rejected_or_ambiguous"

    def _associate(
        self,
        current_geoms: list[dict[str, Any]],
        history_geoms: list[dict[str, Any]],
        image_diag: float,
    ) -> dict[int, int]:
        accepted, _stats = a1_gated_hungarian(
            current_geoms, history_geoms, image_diag
        )
        return {
            current_index: int(detail["history_index"])
            for current_index, detail in accepted.items()
        }


POLICY_NAMES = {
    "disabled": DisabledTemporalPolicy,
    "causal_mean": CausalMeanPolicy,
    "gated_causal": GatedCausalPolicy,
}


def create_temporal_policy(
    policy_name: str,
    *,
    window: int = DEFAULT_WINDOW,
    max_frame_gap: int = DEFAULT_MAX_FRAME_GAP,
    ttl_seconds: float = DEFAULT_TTL_SECONDS,
    now_fn: Optional[Any] = None,
) -> TemporalPolicyProtocol:
    """按名称创建时序策略（manifest 驱动，业务层不硬编码公式）。"""
    if policy_name not in POLICY_NAMES:
        raise ValueError(
            f"不支持的时序策略 {policy_name!r}，可选：{sorted(POLICY_NAMES)}"
        )
    if policy_name == "disabled":
        return DisabledTemporalPolicy()
    policy_cls = POLICY_NAMES[policy_name]
    return policy_cls(
        window=window,
        max_frame_gap=max_frame_gap,
        ttl_seconds=ttl_seconds,
        now_fn=now_fn,
    )
