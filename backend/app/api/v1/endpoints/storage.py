# backend/app/api/v1/endpoints/storage.py
from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings
from app.schemas.base import BaseResponse
from app.services.retention import collect_storage_status
from app.services.storage import StorageError, build_storage

router = APIRouter()


class RuleStatus(BaseModel):
    prefix: str
    keep_days: int
    count: int
    total_bytes: int
    oldest_age_days: Optional[float] = None


class LastCleanup(BaseModel):
    time: str
    deleted: int


class StorageStatusData(BaseModel):
    backend: str
    rules: List[RuleStatus]
    last_cleanup: Optional[LastCleanup] = None


@router.get("/status", response_model=BaseResponse[StorageStatusData])
def get_storage_status() -> BaseResponse[StorageStatusData]:
    """获取存储后端与保留策略状态（只读）。"""
    empty = StorageStatusData(backend=settings.STORAGE_BACKEND, rules=[])
    try:
        storage = build_storage()
        data = collect_storage_status(storage)
    except StorageError as exc:
        return BaseResponse(code=500, msg=f"存储状态获取失败: {exc}", data=empty)

    last = data["last_cleanup"]
    return BaseResponse(
        code=200,
        msg="获取成功",
        data=StorageStatusData(
            backend=settings.STORAGE_BACKEND,
            rules=[RuleStatus(**rule) for rule in data["rules"]],
            last_cleanup=LastCleanup(**last) if last else None,
        ),
    )
