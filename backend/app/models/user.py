from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from app.db.base import Base


class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    userName = Column(String(50), index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=True)
    password = Column(String(100), nullable=False)
    status = Column(Integer, default=1)  # 1: 启用, 0: 禁用
    createTime = Column(DateTime(timezone=True), server_default=func.now())
