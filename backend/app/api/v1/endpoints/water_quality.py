from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from app.schemas.water import (
    WaterQualityCreate,
    WaterQualityResponse,
    WaterQualityHistoryResponse,
)
from app.schemas.base import BaseResponse
from datetime import datetime, timedelta
from app.db.session import get_db
from app.models.water import WaterQualityData

router = APIRouter()


@router.post("/data", response_model=BaseResponse[WaterQualityResponse])
def receive_water_quality_data(data: WaterQualityCreate, db: Session = Depends(get_db)):
    """接收传感器上传的水质数据"""
    db_data = WaterQualityData(
        pond_id=data.pond_id,
        dissolved_oxygen=data.dissolved_oxygen,
        ph_value=data.ph_value,
        temperature=data.temperature,
        ammonia_nitrogen=data.ammonia_nitrogen,
        nitrite=data.nitrite,
        status=data.status,
        collect_time=data.collect_time,
    )
    db.add(db_data)
    db.commit()
    db.refresh(db_data)
    return BaseResponse[WaterQualityResponse](
        code=200, msg="数据接收成功", data=db_data
    )


@router.get("/latest", response_model=BaseResponse[WaterQualityResponse])
def get_latest_water_quality_data(
    pond_id: str = Query(None), db: Session = Depends(get_db)
):
    """获取最新的水质数据"""
    query = db.query(WaterQualityData).order_by(desc(WaterQualityData.collect_time))
    if pond_id:
        query = query.filter(WaterQualityData.pond_id == pond_id)
    record = query.first()
    if not record:
        raise HTTPException(status_code=404, detail="暂无水质数据")
    return BaseResponse[WaterQualityResponse](code=200, msg="获取成功", data=record)


@router.get("/history", response_model=BaseResponse[WaterQualityHistoryResponse])
def get_water_quality_history_data(
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    pond_id: str = Query(None),
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """获取水质历史数据"""
    query = db.query(WaterQualityData)
    if start_time:
        query = query.filter(WaterQualityData.collect_time >= start_time)
    if end_time:
        query = query.filter(WaterQualityData.collect_time <= end_time)
    if pond_id:
        query = query.filter(WaterQualityData.pond_id == pond_id)
    total = query.count()
    records = (
        query.order_by(desc(WaterQualityData.collect_time))
        .offset((page_num - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return BaseResponse[WaterQualityHistoryResponse](
        code=200,
        msg="获取成功",
        data=WaterQualityHistoryResponse(data=records, total=total),
    )


@router.get("/threshold")
def get_water_quality_threshold():
    """获取水质阈值配置"""
    return BaseResponse(
        code=200,
        msg="获取成功",
        data={
            "temperature": {"min": 20, "max": 28},
            "ph": {"min": 6.5, "max": 8.5},
            "dissolved_oxygen": {"min": 5, "max": 15},
            "ammonia_nitrogen": {"min": 0, "max": 0.5},
            "nitrite": {"min": 0, "max": 0.1},
        },
    )
