from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from db.base import Base


class SensorDevice(Base):
    """传感器设备模型"""
    __tablename__ = "sensor_devices"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, unique=True, index=True, nullable=False)
    device_name = Column(String, nullable=False)
    pond_id = Column(String, nullable=False)
    status = Column(String, default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class WaterQualityData(Base):
    """水质数据模型"""
    __tablename__ = "water_quality_data"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String, nullable=False, index=True)
    pond_id = Column(String, nullable=False, index=True)
    dissolved_oxygen = Column(Float, nullable=False)
    ph_value = Column(Float, nullable=False)
    temperature = Column(Float, nullable=False)
    ammonia_nitrogen = Column(Float, nullable=False)
    analysis_result = Column(String, nullable=True)
    alert_level = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AlertRecord(Base):
    """预警记录模型"""
    __tablename__ = "alert_records"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String, nullable=False)
    pond_id = Column(String, nullable=False)
    alert_type = Column(String, nullable=False)
    alert_message = Column(String, nullable=False)
    alert_level = Column(String, nullable=False)
    is_resolved = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
