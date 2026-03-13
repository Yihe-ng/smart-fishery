from sqlalchemy.orm import Session
from app.models.water import WaterQualityData, SensorDevice, AlertRecord
from app.schemas.water import WaterQualityCreate
from datetime import datetime


def create_water_quality_data(db: Session, data: WaterQualityCreate, analysis_result: str, alert_level: str):
    """创建水质数据记录"""
    db_data = WaterQualityData(
        sensor_id=data.sensor_id,
        pond_id=data.pond_id,
        dissolved_oxygen=data.dissolved_oxygen,
        ph_value=data.ph_value,
        temperature=data.temperature,
        ammonia_nitrogen=data.ammonia_nitrogen,
        analysis_result=analysis_result,
        alert_level=alert_level
    )
    db.add(db_data)
    db.commit()
    db.refresh(db_data)
    return db_data


def get_latest_water_quality(db: Session, sensor_id: str = None, pond_id: str = None):
    """获取最新的水质数据"""
    query = db.query(WaterQualityData)
    if sensor_id:
        query = query.filter(WaterQualityData.sensor_id == sensor_id)
    if pond_id:
        query = query.filter(WaterQualityData.pond_id == pond_id)
    return query.order_by(WaterQualityData.created_at.desc()).first()


def get_water_quality_history(db: Session, start_time: datetime, end_time: datetime, 
                            sensor_id: str = None, pond_id: str = None, 
                            skip: int = 0, limit: int = 100):
    """获取水质历史数据"""
    query = db.query(WaterQualityData).filter(
        WaterQualityData.created_at >= start_time,
        WaterQualityData.created_at <= end_time
    )
    if sensor_id:
        query = query.filter(WaterQualityData.sensor_id == sensor_id)
    if pond_id:
        query = query.filter(WaterQualityData.pond_id == pond_id)
    
    total = query.count()
    data = query.order_by(WaterQualityData.created_at.desc()).offset(skip).limit(limit).all()
    
    return data, total


def create_sensor_device(db: Session, device_id: str, device_name: str, pond_id: str):
    """创建设备记录"""
    db_device = SensorDevice(
        device_id=device_id,
        device_name=device_name,
        pond_id=pond_id,
        status="active"
    )
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device


def get_sensor_devices(db: Session, skip: int = 0, limit: int = 100):
    """获取所有传感器设备"""
    return db.query(SensorDevice).offset(skip).limit(limit).all()


def create_alert_record(db: Session, sensor_id: str, pond_id: str, alert_type: str, 
                       alert_message: str, alert_level: str):
    """创建预警记录"""
    db_alert = AlertRecord(
        sensor_id=sensor_id,
        pond_id=pond_id,
        alert_type=alert_type,
        alert_message=alert_message,
        alert_level=alert_level,
        is_resolved=0
    )
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert
