from sqlalchemy.orm import Session
from app.schemas.water import WaterQualityCreate
from crud.crud_water import create_water_quality_data, get_latest_water_quality, get_water_quality_history
from algorithms.prediction import analyze_water_quality


def process_water_quality_data(db: Session, data: WaterQualityCreate):
    """处理水质数据
    
    1. 调用算法分析水质
    2. 存储数据到数据库
    3. 处理预警
    """
    # 调用算法分析水质
    analysis_data = {
        'dissolved_oxygen': data.dissolved_oxygen,
        'ph_value': data.ph_value,
        'temperature': data.temperature,
        'ammonia_nitrogen': data.ammonia_nitrogen
    }
    analysis_result = analyze_water_quality(analysis_data)
    
    # 存储数据到数据库
    db_data = create_water_quality_data(
        db=db,
        data=data,
        analysis_result=analysis_result['analysis_result'],
        alert_level=analysis_result['alert_level']
    )
    
    # 处理预警（如果需要）
    if analysis_result['alert_level'] in ['high', 'critical']:
        # 这里可以添加预警处理逻辑
        pass
    
    return db_data


def get_latest_water_quality_service(db: Session, sensor_id: str = None, pond_id: str = None):
    """获取最新水质数据服务"""
    return get_latest_water_quality(db, sensor_id, pond_id)


def get_water_quality_history_service(db: Session, start_time, end_time, 
                                    sensor_id: str = None, pond_id: str = None, 
                                    skip: int = 0, limit: int = 100):
    """获取水质历史数据服务"""
    return get_water_quality_history(db, start_time, end_time, sensor_id, pond_id, skip, limit)
