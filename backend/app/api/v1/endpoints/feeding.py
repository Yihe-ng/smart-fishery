from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.agent.preview_store import (
    mark_manual_feeding_preview_executed,
    validate_manual_feeding_preview_snapshot,
)
from app.agent.schemas import ManualFeedingExecuteRequest
from app.schemas.base import BaseResponse, PageResult
from app.services.smart_feeding import smart_feeding_service
from app.websocket.manager import manager

router = APIRouter()


class FeedingConfig(BaseModel):
    feed_coefficient: float
    frequency: int
    feed_size: str


class FeedingLogBase(BaseModel):
    feed_time: str
    amount: int
    status: str
    trigger_type: str


class FeedingLogResponse(FeedingLogBase):
    id: str


class SmartFeedingRequest(BaseModel):
    pond_id: str
    fish_count: int = 1000
    avg_fish_weight: float = 300


class SmartFeedingResponse(BaseModel):
    can_feed: bool
    pond_id: str
    recommended_amount: Optional[float] = None
    optimal_time: Optional[str] = None
    confidence: Optional[float] = None
    factors: Optional[dict] = None
    water_quality: Optional[dict] = None
    suggestion: Optional[str] = None
    estimated_duration: Optional[int] = None
    reason: Optional[str] = None


mock_feeding_config = {
    "feed_coefficient": 1.6,
    "frequency": 3,
    "feed_size": "2.0mm",
}

mock_feeding_logs = [
    {
        "id": "1",
        "feed_time": "2024-03-20 08:00:00",
        "amount": 500,
        "status": "completed",
        "trigger_type": "auto",
    },
    {
        "id": "2",
        "feed_time": "2024-03-20 12:00:00",
        "amount": 500,
        "status": "completed",
        "trigger_type": "auto",
    },
    {
        "id": "3",
        "feed_time": "2024-03-20 18:00:00",
        "amount": 600,
        "status": "pending",
        "trigger_type": "manual",
    },
]


@router.get("/config", response_model=BaseResponse[FeedingConfig])
async def get_feeding_config():
    return BaseResponse[FeedingConfig](
        code=200,
        msg="获取成功",
        data=FeedingConfig(**mock_feeding_config),
    )


@router.post("/config", response_model=BaseResponse[dict])
async def update_feeding_config(config: FeedingConfig):
    global mock_feeding_config
    mock_feeding_config["feed_coefficient"] = config.feed_coefficient
    mock_feeding_config["frequency"] = config.frequency
    mock_feeding_config["feed_size"] = config.feed_size

    return BaseResponse[dict](code=200, msg="更新成功", data={"updated": True})


@router.get("/logs", response_model=BaseResponse[PageResult[FeedingLogResponse]])
async def get_feeding_logs(
    pageNum: int = Query(1, description="当前页码"),
    pageSize: int = Query(10, description="每页大小"),
    status: Optional[str] = Query(None, description="状态筛选"),
):
    filtered_logs = mock_feeding_logs.copy()

    if status:
        filtered_logs = [log for log in filtered_logs if log["status"] == status]

    total = len(filtered_logs)
    start = (pageNum - 1) * pageSize
    end = start + pageSize
    page_data = filtered_logs[start:end]

    return BaseResponse[PageResult[FeedingLogResponse]](
        code=200,
        msg="获取成功",
        data=PageResult[FeedingLogResponse](
            total=total,
            list=[FeedingLogResponse(**log) for log in page_data],
        ),
    )


@router.post("/manual", response_model=BaseResponse[dict])
async def manual_feeding(amount: int = Query(..., description="投喂量（克）")):
    new_log = {
        "id": str(len(mock_feeding_logs) + 1),
        "feed_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "amount": amount,
        "status": "completed",
        "trigger_type": "manual",
    }
    mock_feeding_logs.insert(0, new_log)

    return BaseResponse[dict](
        code=200,
        msg="投喂成功",
        data={"id": new_log["id"], "amount": amount},
    )


@router.post("/smart", response_model=BaseResponse[SmartFeedingResponse])
async def smart_feeding(request: SmartFeedingRequest):
    result = smart_feeding_service.calculate_feeding_plan(
        pond_id=request.pond_id,
        fish_count=request.fish_count,
        avg_fish_weight=request.avg_fish_weight,
    )

    return BaseResponse[SmartFeedingResponse](
        code=200,
        msg="智能投喂决策完成",
        data=SmartFeedingResponse(**result),
    )


@router.post("/execute", response_model=BaseResponse[dict])
async def execute_feeding(request: ManualFeedingExecuteRequest):
    try:
        snapshot = validate_manual_feeding_preview_snapshot(
            confirm_token=request.confirmToken,
            feeder_id=request.feederId,
            amount=request.amount,
            duration=request.duration,
            pond_id=request.pondId,
        )
        result = await smart_feeding_service.execute_feeding(
            feeder_id=snapshot.feeder_id,
            amount=snapshot.amount,
            duration=snapshot.duration,
        )

        if result["success"]:
            mark_manual_feeding_preview_executed(request.confirmToken)
            return BaseResponse[dict](
                code=200,
                msg="投喂指令已下发",
                data=result,
            )

        raise HTTPException(status_code=400, detail=result["error"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"投喂指令发送失败: {str(exc)}")


@router.get("/devices/online", response_model=BaseResponse[List[str]])
async def get_online_feeders():
    online_devices = manager.get_online_devices(device_type="feeder")
    return BaseResponse[List[str]](code=200, msg="获取成功", data=online_devices)


@router.get("/devices/{feeder_id}/status", response_model=BaseResponse[dict])
async def get_feeder_status(feeder_id: str):
    status = manager.get_device_status(feeder_id)
    if not status:
        raise HTTPException(status_code=404, detail="设备不存在或未连接")

    return BaseResponse[dict](code=200, msg="获取成功", data=status)
