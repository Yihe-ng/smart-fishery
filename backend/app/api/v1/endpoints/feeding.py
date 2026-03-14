from fastapi import APIRouter, HTTPException, Query
from app.schemas.base import BaseResponse, PageQuery, PageResult
from app.services.smart_feeding import smart_feeding_service
from app.websocket.manager import manager
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter()


class FeedingConfig(BaseModel):
    """投喂配置模型"""
    feed_coefficient: float  # 饲料系数
    frequency: int            # 每日投喂次数
    feed_size: str           # 饲料粒径


class FeedingLogBase(BaseModel):
    """投喂日志基础模型"""
    feed_time: str
    amount: int
    status: str
    trigger_type: str


class FeedingLogResponse(FeedingLogBase):
    """投喂日志响应模型"""
    id: str


class SmartFeedingRequest(BaseModel):
    """智能投喂请求"""
    pond_id: str
    fish_count: int = 1000
    avg_fish_weight: float = 300  # 克


class SmartFeedingResponse(BaseModel):
    """智能投喂响应"""
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


# 模拟投喂配置
mock_feeding_config = {
    "feed_coefficient": 1.6,
    "frequency": 3,
    "feed_size": "2.0mm"
}

# 模拟投喂日志
mock_feeding_logs = [
    {
        "id": "1",
        "feed_time": "2024-03-20 08:00:00",
        "amount": 500,
        "status": "completed",
        "trigger_type": "auto"
    },
    {
        "id": "2",
        "feed_time": "2024-03-20 12:00:00",
        "amount": 500,
        "status": "completed",
        "trigger_type": "auto"
    },
    {
        "id": "3",
        "feed_time": "2024-03-20 18:00:00",
        "amount": 600,
        "status": "pending",
        "trigger_type": "manual"
    }
]


@router.get("/config", response_model=BaseResponse[FeedingConfig])
async def get_feeding_config():
    """异步获取投喂配置"""
    return BaseResponse[FeedingConfig](
        code=200,
        msg="获取成功",
        data=FeedingConfig(**mock_feeding_config)
    )


@router.post("/config", response_model=BaseResponse[dict])
async def update_feeding_config(config: FeedingConfig):
    """异步更新投喂配置"""
    global mock_feeding_config
    mock_feeding_config["feed_coefficient"] = config.feed_coefficient
    mock_feeding_config["frequency"] = config.frequency
    mock_feeding_config["feed_size"] = config.feed_size
    
    return BaseResponse[dict](
        code=200,
        msg="更新成功",
        data={"updated": True}
    )


@router.get("/logs", response_model=BaseResponse[PageResult[FeedingLogResponse]])
async def get_feeding_logs(
    pageNum: int = Query(1, description="当前页码"),
    pageSize: int = Query(10, description="每页大小"),
    status: Optional[str] = Query(None, description="状态筛选")
):
    """异步获取投喂日志"""
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
            list=[FeedingLogResponse(**log) for log in page_data]
        )
    )


@router.post("/manual", response_model=BaseResponse[dict])
async def manual_feeding(amount: int = Query(..., description="投喂量（克）")):
    """异步手动投喂"""
    new_log = {
        "id": str(len(mock_feeding_logs) + 1),
        "feed_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "amount": amount,
        "status": "completed",
        "trigger_type": "manual"
    }
    mock_feeding_logs.insert(0, new_log)
    
    return BaseResponse[dict](
        code=200,
        msg="投喂成功",
        data={"id": new_log["id"], "amount": amount}
    )


# ==================== 智能投喂接口 ====================

@router.post("/smart", response_model=BaseResponse[SmartFeedingResponse])
async def smart_feeding(
    request: SmartFeedingRequest
):
    """
    智能投喂决策接口
    
    根据当前水质、鱼类密度等因素，智能计算最佳投喂量和时间
    """
    result = await smart_feeding_service.calculate_feeding_plan(
        pond_id=request.pond_id,
        fish_count=request.fish_count,
        avg_fish_weight=request.avg_fish_weight
    )
    
    return BaseResponse[SmartFeedingResponse](
        code=200,
        msg="智能投喂决策完成",
        data=SmartFeedingResponse(**result)
    )


@router.post("/execute", response_model=BaseResponse[dict])
async def execute_feeding(
    feeder_id: str = Query(..., description="投喂设备ID"),
    amount: float = Query(..., description="投喂量(g)"),
    duration: int = Query(10, description="投喂持续时间(秒)")
):
    """
    执行投喂指令（通过 WebSocket）
    
    向投喂设备发送实时控制指令
    """
    try:
        result = await smart_feeding_service.execute_feeding(
            feeder_id=feeder_id,
            amount=amount,
            duration=duration
        )
        
        if result['success']:
            return BaseResponse[dict](
                code=200,
                msg="投喂指令已下发",
                data=result
            )
        else:
            raise HTTPException(status_code=400, detail=result['error'])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"投喂指令发送失败: {str(e)}")


@router.get("/devices/online", response_model=BaseResponse[List[str]])
async def get_online_feeders():
    """获取在线投喂设备列表"""
    online_devices = manager.get_online_devices(device_type='feeder')
    return BaseResponse[List[str]](
        code=200,
        msg="获取成功",
        data=online_devices
    )


@router.get("/devices/{feeder_id}/status", response_model=BaseResponse[dict])
async def get_feeder_status(feeder_id: str):
    """获取投喂设备状态"""
    status = manager.get_device_status(feeder_id)
    if not status:
        raise HTTPException(status_code=404, detail="设备不存在或未连接")
    
    return BaseResponse[dict](
        code=200,
        msg="获取成功",
        data=status
    )
