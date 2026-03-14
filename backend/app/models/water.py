from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.base import Base


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
    dissolved_oxygen = Column(Float, nullable=False)  # 溶解氧 mg/L
    ph_value = Column(Float, nullable=False)          # pH值
    temperature = Column(Float, nullable=False)       # 温度 ℃
    ammonia_nitrogen = Column(Float, nullable=False)  # 氨氮 mg/L
    nitrite = Column(Float, nullable=False)           # 亚硝酸盐 mg/L
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
