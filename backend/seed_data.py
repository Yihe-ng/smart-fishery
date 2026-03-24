import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from datetime import datetime
from app.db.session import engine, SessionLocal
from app.db.base import Base
from app.models.user import User
from app.models.water import WaterQualityData, AlertRecord


def init_db():
    Base.metadata.create_all(bind=engine)
    print("数据库表已创建")


def seed_users(db):
    users = [
        {
            "id": 1,
            "userName": "Super",
            "email": "super@example.com",
            "phone": "13800138000",
            "password": "123456",
            "role": "super_admin",
            "status": 1,
        },
        {
            "id": 2,
            "userName": "Admin",
            "email": "admin@example.com",
            "phone": "13800138001",
            "password": "123456",
            "role": "admin",
            "status": 1,
        },
        {
            "id": 3,
            "userName": "User",
            "email": "user@example.com",
            "phone": "13800138002",
            "password": "123456",
            "role": "user",
            "status": 1,
        },
    ]
    for u in users:
        user = User(**u, createTime=datetime(2024, 1, 1))
        db.add(user)
    db.commit()
    print(f"已导入 {len(users)} 个用户")


def seed_water_quality(db):
    df = pd.read_excel("D:/文件/易找的文件/智慧渔业/文档/水质数据.xlsx")
    count = 0
    for _, row in df.iterrows():
        data = WaterQualityData(
            pond_id=row["塘口编号"],
            dissolved_oxygen=row["溶氧(mg/L)"],
            ph_value=row["pH值"],
            temperature=row["水温(℃)"],
            ammonia_nitrogen=row["氨氮(mg/L)"],
            nitrite=row["亚硝酸盐(mg/L)"],
            status=row["状态"],
            collect_time=row["时间戳"],
        )
        db.add(data)
        count += 1
    db.commit()
    print(f"已导入 {count} 条水质数据")


def seed_alerts(db):
    abnormal_records = (
        db.query(WaterQualityData).filter(WaterQualityData.status == "异常").all()
    )
    count = 0
    for record in abnormal_records:
        alert = AlertRecord(
            pond_id=record.pond_id,
            alert_type="water_quality",
            alert_message=f"水质异常: 溶氧{record.dissolved_oxygen}, pH{record.ph_value}, 氨氮{record.ammonia_nitrogen}, 亚硝酸盐{record.nitrite}",
            alert_level="warning",
            is_resolved=0,
            collect_time=record.collect_time,
        )
        db.add(alert)
        count += 1
    db.commit()
    print(f"已生成 {count} 条告警记录")


if __name__ == "__main__":
    init_db()
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            seed_users(db)
        else:
            print("用户数据已存在，跳过")
        if db.query(WaterQualityData).count() == 0:
            seed_water_quality(db)
        else:
            print("水质数据已存在，跳过")
        if db.query(AlertRecord).count() == 0:
            seed_alerts(db)
        else:
            print("告警数据已存在，跳过")
        print("数据导入完成")
    finally:
        db.close()
