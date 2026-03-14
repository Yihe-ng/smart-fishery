"""异步水质数据 CRUD 操作"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.models.water import WaterQualityData, SensorDevice, AlertRecord
from app.schemas.water import WaterQualityCreate
from datetime import datetime
from typing import Optional, List, Tuple


async def create_water_quality_data(
    db: AsyncSession, 
    data: WaterQualityCreate, 
    analysis_result: str, 
    alert_level: str
) -> WaterQualityData:
    """异步创建水质数据记录"""
    db_data = WaterQualityData(
        sensor_id=data.sensor_id,
        pond_id=data.pond_id,
        dissolved_oxygen=data.dissolved_oxygen,
        ph_value=data.ph_value,
        temperature=data.temperature,
        ammonia_nitrogen=data.ammonia_nitrogen,
        nitrite=data.nitrite,
        analysis_result=analysis_result,
        alert_level=alert_level
    )
    db.add(db_data)
    await db.commit()
    await db.refresh(db_data)
    return db_data


async def get_latest_water_quality(
    db: AsyncSession, 
    sensor_id: Optional[str] = None, 
    pond_id: Optional[str] = None
) -> Optional[WaterQualityData]:
    """异步获取最新的水质数据"""
    query = select(WaterQualityData).order_by(desc(WaterQualityData.created_at))
    
    if sensor_id:
        query = query.where(WaterQualityData.sensor_id == sensor_id)
    if pond_id:
        query = query.where(WaterQualityData.pond_id == pond_id)
    
    result = await db.execute(query.limit(1))
    return result.scalar_one_or_none()


async def get_water_quality_history(
    db: AsyncSession,
    start_time: datetime,
    end_time: datetime,
    sensor_id: Optional[str] = None,
    pond_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> Tuple[List[WaterQualityData], int]:
    """异步获取水质历史数据"""
    # 构建基础查询
    base_query = select(WaterQualityData).where(
        WaterQualityData.created_at >= start_time,
        WaterQualityData.created_at <= end_time
    )
    
    if sensor_id:
        base_query = base_query.where(WaterQualityData.sensor_id == sensor_id)
    if pond_id:
        base_query = base_query.where(WaterQualityData.pond_id == pond_id)
    
    # 获取总数
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 获取分页数据
    data_query = base_query.order_by(desc(WaterQualityData.created_at)).offset(skip).limit(limit)
    result = await db.execute(data_query)
    data = result.scalars().all()
    
    return list(data), total


async def get_alert_records(
    db: AsyncSession,
    alert_level: Optional[str] = None,
    limit: int = 10
) -> List[AlertRecord]:
    """异步获取告警记录"""
    query = select(AlertRecord).order_by(desc(AlertRecord.created_at))
    
    if alert_level:
        query = query.where(AlertRecord.alert_level == alert_level)
    
    result = await db.execute(query.limit(limit))
    return list(result.scalars().all())


async def create_alert_record(
    db: AsyncSession,
    water_quality_id: int,
    alert_level: str,
    alert_message: str
) -> AlertRecord:
    """异步创建告警记录"""
    alert = AlertRecord(
        water_quality_id=water_quality_id,
        alert_level=alert_level,
        alert_message=alert_message
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return alert
