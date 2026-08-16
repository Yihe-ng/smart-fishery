"""数据保留策略层：按规则清理过期存储对象（原始图像/视频等）。

职责：对上层隐藏"什么时候删"。与存储后端解耦，只依赖 StorageBackend 的
list_keys / modified_time / delete。规则由配置驱动（config.py 的
STORAGE_*_RETENTION_DAYS），未配置或天数 <=0 时 enforce_retention 为空操作，
不影响现有推理链路。

用法：
    policy = RetentionPolicy.from_settings()
    deleted = enforce_retention(storage, policy)
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from app.core.config import settings
from app.services.storage import StorageBackend, StorageError

logger = logging.getLogger(__name__)

DELETE = "delete"

_SECONDS_PER_DAY = 24 * 60 * 60

# 清理标记对象键：记录最近一次保留策略执行，前缀规则不会覆盖到 _meta/。
_CLEANUP_MARKER_KEY = "_meta/cleanup.json"

# 前缀 → 配置项名：用于从 Settings 构建默认策略。
# 对应配置项 <=0 表示该前缀不启用保留清理。
_RETENTION_SETTINGS: List[Tuple[str, str]] = [
    ("raw/", "STORAGE_RAW_RETENTION_DAYS"),
    ("results/", "STORAGE_RESULTS_RETENTION_DAYS"),
    ("archive/", "STORAGE_ARCHIVE_RETENTION_DAYS"),
]


@dataclass(frozen=True)
class RetentionRule:
    """单条保留规则：前缀匹配 + 保留天数 + 动作（当前仅支持 delete）。"""

    prefix: str
    keep_days: int
    action: str = DELETE

    def __post_init__(self) -> None:
        if self.keep_days < 0:
            raise ValueError(f"keep_days 不能为负: {self.keep_days}")
        if self.action != DELETE:
            raise ValueError(f"暂不支持的保留动作: {self.action!r}（当前仅支持 {DELETE!r}）")


@dataclass(frozen=True)
class RetentionPolicy:
    """保留策略 = 规则集合；enforce_retention 按顺序对每条规则执行。"""

    rules: Tuple[RetentionRule, ...] = ()

    @classmethod
    def from_settings(cls, settings_obj=None) -> "RetentionPolicy":
        """从 Settings 构建默认策略；天数 <=0 的前缀自动跳过。"""
        cfg = settings_obj or settings
        rules = []
        for prefix, attr in _RETENTION_SETTINGS:
            days = getattr(cfg, attr, 0) or 0
            if days > 0:
                rules.append(RetentionRule(prefix=prefix, keep_days=days))
        return cls(rules=tuple(rules))


def enforce_retention(
    storage: StorageBackend, policy: RetentionPolicy, now: Optional[float] = None
) -> int:
    """执行保留策略，返回删除的对象数。now 仅用于测试注入时间。"""
    current = now if now is not None else time.time()
    deleted = 0
    for rule in policy.rules:
        for key in storage.list_keys(rule.prefix):
            try:
                age_days = (current - storage.modified_time(key)) / _SECONDS_PER_DAY
            except StorageError:
                logger.debug("跳过保留检查（对象不可读）: %s", key)
                continue
            if age_days >= rule.keep_days:
                storage.delete(key)
                deleted += 1
                logger.info("保留策略删除过期对象: %s（%.1f 天）", key, age_days)
    return deleted


def collect_storage_status(
    storage: StorageBackend,
    policy: Optional[RetentionPolicy] = None,
    now: Optional[float] = None,
) -> Dict:
    """汇总各保留前缀的用量与保留规则，供数据管理页展示。

    返回 {"rules": [{prefix, keep_days, count, total_bytes, oldest_age_days}],
    "last_cleanup": {"time", "deleted"} | None}。oldest_age_days 为该前缀
    最老对象距今的天数；前缀为空时 oldest_age_days 为 None。
    """
    policy = policy or RetentionPolicy.from_settings()
    current = now if now is not None else time.time()
    rules_usage = []
    for rule in policy.rules:
        keys = storage.list_keys(rule.prefix)
        total_bytes = 0
        oldest_ts: Optional[float] = None
        for key in keys:
            try:
                total_bytes += storage.size_of(key)
            except StorageError:
                logger.debug("跳过大小统计（对象不可读）: %s", key)
            try:
                mtime = storage.modified_time(key)
            except StorageError:
                continue
            oldest_ts = mtime if oldest_ts is None else min(oldest_ts, mtime)
        rules_usage.append(
            {
                "prefix": rule.prefix,
                "keep_days": rule.keep_days,
                "count": len(keys),
                "total_bytes": total_bytes,
                "oldest_age_days": (
                    round((current - oldest_ts) / _SECONDS_PER_DAY, 2)
                    if oldest_ts is not None
                    else None
                ),
            }
        )
    return {"rules": rules_usage, "last_cleanup": get_last_cleanup(storage)}


def record_last_cleanup(storage: StorageBackend, deleted: int) -> None:
    """将最近一次保留策略执行记录持久化到 _meta/cleanup.json。"""
    payload = json.dumps(
        {
            "time": datetime.now(timezone.utc).isoformat(),
            "deleted": deleted,
        }
    ).encode("utf-8")
    storage.save_bytes(_CLEANUP_MARKER_KEY, payload)


def get_last_cleanup(storage: StorageBackend) -> Optional[Dict]:
    """读取最近一次保留策略执行记录；从未执行过返回 None。"""
    try:
        raw = storage.read_bytes(_CLEANUP_MARKER_KEY)
    except StorageError:
        return None
    try:
        data = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        logger.warning("清理标记文件无法解析，忽略: %s", _CLEANUP_MARKER_KEY)
        return None
    return data if isinstance(data, dict) else None
