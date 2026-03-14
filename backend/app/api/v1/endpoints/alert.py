from fastapi import APIRouter, HTTPException, Query
from app.schemas.base import BaseResponse, PageQuery, PageResult
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter()


class AlertBase(BaseModel):
    """告警基础模型"""
    type: str
    level: str
    title: str
    message: str
    status: str
    related_device: Optional[str] = None


class AlertResponse(AlertBase):
    """告警响应模型"""
    id: str
    create_time: str


# 模拟告警数据
mock_alerts = [
    {
        "id": "1",
        "type": "water_quality",
        "level": "warning",
        "title": "水温偏高",
        "message": "当前水温 28.5℃，超过阈值 28.0℃",
        "create_time": datetime.now().isoformat(),
        "status": "pending",
        "related_device": "temp-001"
    },
    {
        "id": "2",
        "type": "device_offline",
        "level": "critical",
        "title": "传感器离线",
        "message": "亚硝酸盐传感器已离线",
        "create_time": datetime.now().isoformat(),
        "status": "pending",
        "related_device": "no2-001"
    },
    {
        "id": "3",
        "type": "disease_detected",
        "level": "warning",
        "title": "检测到病害",
        "message": "检测到疑似烂鳃症状",
        "create_time": datetime.now().isoformat(),
        "status": "resolved",
        "related_device": "camera-001"
    }
]


@router.get("/recent", response_model=BaseResponse[List[AlertResponse]])
def get_recent_alerts(count: int = Query(5, description="获取最近告警数量")):
    """获取最近告警"""
    return BaseResponse[List[AlertResponse]](
        code=200,
        msg="获取成功",
        data=[AlertResponse(**alert) for alert in mock_alerts[:count]]
    )


@router.get("/list", response_model=BaseResponse[PageResult[AlertResponse]])
def get_alert_list(
    pageNum: int = Query(1, description="当前页码"),
    pageSize: int = Query(10, description="每页大小"),
    level: Optional[str] = Query(None, description="告警级别筛选"),
    status: Optional[str] = Query(None, description="状态筛选")
):
    """获取告警列表（分页）"""
    filtered_alerts = mock_alerts.copy()
    
    if level:
        filtered_alerts = [a for a in filtered_alerts if a["level"] == level]
    
    if status:
        filtered_alerts = [a for a in filtered_alerts if a["status"] == status]
    
    total = len(filtered_alerts)
    start = (pageNum - 1) * pageSize
    end = start + pageSize
    page_data = filtered_alerts[start:end]
    
    return BaseResponse[PageResult[AlertResponse]](
        code=200,
        msg="获取成功",
        data=PageResult[AlertResponse](
            total=total,
            list=[AlertResponse(**alert) for alert in page_data]
        )
    )


@router.post("/{alert_id}/resolve", response_model=BaseResponse[dict])
def resolve_alert(alert_id: str):
    """确认/忽略告警"""
    alert = next((a for a in mock_alerts if a["id"] == alert_id), None)
    if not alert:
        raise HTTPException(status_code=404, detail="告警不存在")
    
    alert["status"] = "resolved"
    
    return BaseResponse[dict](
        code=200,
        msg="处理成功",
        data={"id": alert_id, "status": "resolved"}
    )
