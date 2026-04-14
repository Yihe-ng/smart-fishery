from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ManualFeedingPreviewSnapshot:
    confirm_token: str
    pond_id: str | None
    feeder_id: str
    amount: float
    duration: int
    expires_at: str
    executed: bool = False


_preview_snapshots: dict[str, ManualFeedingPreviewSnapshot] = {}


def _cleanup_expired_snapshots() -> None:
    now = datetime.now()
    expired_tokens = [
        token
        for token, snapshot in _preview_snapshots.items()
        if datetime.fromisoformat(snapshot.expires_at) <= now
    ]
    for token in expired_tokens:
        _preview_snapshots.pop(token, None)


def save_manual_feeding_preview_snapshot(
    *,
    confirm_token: str,
    pond_id: str | None,
    feeder_id: str,
    amount: float,
    duration: int,
    expires_at: str,
) -> ManualFeedingPreviewSnapshot:
    _cleanup_expired_snapshots()
    snapshot = ManualFeedingPreviewSnapshot(
        confirm_token=confirm_token,
        pond_id=pond_id,
        feeder_id=feeder_id,
        amount=amount,
        duration=duration,
        expires_at=expires_at,
    )
    _preview_snapshots[confirm_token] = snapshot
    return snapshot


def validate_manual_feeding_preview_snapshot(
    *,
    confirm_token: str,
    feeder_id: str,
    amount: float,
    duration: int,
    pond_id: str | None = None,
) -> ManualFeedingPreviewSnapshot:
    _cleanup_expired_snapshots()
    snapshot = _preview_snapshots.get(confirm_token)
    if snapshot is None:
        raise ValueError("确认令牌无效或对应预览不存在")
    if snapshot.executed:
        raise ValueError("该预览已执行，请重新生成预览")
    if pond_id is not None and snapshot.pond_id != pond_id:
        raise ValueError("执行参数与预览快照不一致")
    if snapshot.feeder_id != feeder_id:
        raise ValueError("执行参数与预览快照不一致")
    if abs(snapshot.amount - amount) >= 0.01:
        raise ValueError("执行参数与预览快照不一致")
    if snapshot.duration != duration:
        raise ValueError("执行参数与预览快照不一致")
    return snapshot


def mark_manual_feeding_preview_executed(confirm_token: str) -> None:
    snapshot = _preview_snapshots.get(confirm_token)
    if snapshot is None:
        raise ValueError("确认令牌无效或对应预览不存在")
    snapshot.executed = True
