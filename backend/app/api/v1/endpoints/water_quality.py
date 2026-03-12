from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.water import (
    WaterQualityCreate, WaterQualityResponse, 
    WaterQualityHistoryRequest, WaterQualityHistoryResponse
)
from services.water_analysis import (
    process_water_quality_data,
    get_latest_water_quality_service,
    get_water_quality_history_service
)
from db.session import get_db
from models.base import BaseResponse
from datetime import datetime

router = APIRouter()

@router.post("/data", response_model=BaseResponse[WaterQualityResponse])
def receive_water_quality_data(
    data: WaterQualityCreate,
    db: Session = Depends(get_db)
):
    """接收传感器上传的水质数据"""
    try:
        # 处理数据（调用算法分析并存储）
        result = process_water_quality_data(db, data)
        return BaseResponse[WaterQualityResponse](
            code=200,
            msg="数据接收成功",
            data=result
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"数据处理失败: {str(e)}"
        )

@router.get("/latest", response_model=BaseResponse[WaterQualityResponse])
def get_latest_water_quality(
    sensor_id: str = None,
    pond_id: str = None,
    db: Session = Depends(get_db)
):
    """获取最新的水质数据"""
    result = get_latest_water_quality_service(db, sensor_id, pond_id)
    if not result:
        raise HTTPException(
            status_code=404,
            detail="未找到水质数据"
        )
    return BaseResponse[WaterQualityResponse](
        code=200,
        msg="获取成功",
        data=result
    )

@router.post("/history", response_model=BaseResponse[WaterQualityHistoryResponse])
def get_water_quality_history(
    request: WaterQualityHistoryRequest,
    db: Session = Depends(get_db)
):
    """获取水质历史数据"""
    data, total = get_water_quality_history_service(
        db,
        start_time=request.start_time,
        end_time=request.end_time,
        sensor_id=request.sensor_id,
        pond_id=request.pond_id
    )
    return BaseResponse[WaterQualityHistoryResponse](
        code=200,
        msg="获取成功",
        data=WaterQualityHistoryResponse(
            data=data,
            total=total
        )
    )
