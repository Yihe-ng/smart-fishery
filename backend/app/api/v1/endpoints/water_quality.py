from fastapi import APIRouter, HTTPException, Query
from app.schemas.water import (
    WaterQualityCreate, WaterQualityResponse,
    WaterQualityHistoryResponse
)
from pydantic import BaseModel
from app.schemas.base import BaseResponse
from datetime import datetime, timedelta
from algorithms.prediction import analyze_water_quality

router = APIRouter()


@router.post("/data", response_model=BaseResponse[WaterQualityResponse])
async def receive_water_quality_data(
    data: WaterQualityCreate
):
    """异步接收传感器上传的水质数据"""
    try:
        # 调用算法分析水质
        analysis_result = analyze_water_quality({
            'dissolved_oxygen': data.dissolved_oxygen,
            'ph_value': data.ph_value,
            'temperature': data.temperature,
            'ammonia_nitrogen': data.ammonia_nitrogen,
            'nitrite': data.nitrite
        })

        # 模拟数据
        mock_data = {
            'id': 1,
            'sensor_id': data.sensor_id,
            'pond_id': data.pond_id,
            'dissolved_oxygen': data.dissolved_oxygen,
            'ph_value': data.ph_value,
            'temperature': data.temperature,
            'ammonia_nitrogen': data.ammonia_nitrogen,
            'nitrite': data.nitrite,
            'analysis_result': analysis_result['analysis_result'],
            'alert_level': analysis_result['alert_level'],
            'created_at': datetime.now().isoformat()
        }

        return BaseResponse[WaterQualityResponse](
            code=200,
            msg="数据接收成功",
            data=WaterQualityResponse(**mock_data)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"数据处理失败: {str(e)}"
        )


@router.get("/latest", response_model=BaseResponse[WaterQualityResponse])
async def get_latest_water_quality_data(
    sensor_id: str = Query(None, description="传感器ID"),
    pond_id: str = Query(None, description="鱼塘ID")
):
    """异步获取最新的水质数据"""
    # 模拟数据
    mock_data = {
        'id': 1,
        'sensor_id': sensor_id or 'sensor-001',
        'pond_id': pond_id or '1',
        'dissolved_oxygen': 6.8,
        'ph_value': 7.2,
        'temperature': 25.5,
        'ammonia_nitrogen': 0.3,
        'nitrite': 0.05,
        'analysis_result': '水质良好',
        'alert_level': 'normal',
        'created_at': datetime.now().isoformat()
    }

    return BaseResponse[WaterQualityResponse](
        code=200,
        msg="获取成功",
        data=WaterQualityResponse(**mock_data)
    )


@router.get("/history", response_model=BaseResponse[WaterQualityHistoryResponse])
async def get_water_quality_history_data(
    start_time: datetime = Query(..., description="开始时间"),
    end_time: datetime = Query(..., description="结束时间"),
    sensor_id: str = Query(None, description="传感器ID"),
    pond_id: str = Query(None, description="鱼塘ID"),
    page_num: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页大小")
):
    """
    获取水质历史数据（使用 GET 请求）
    
    符合 RESTful 设计原则：
    - 使用 GET 方法获取资源
    - 可被浏览器和代理缓存
    - 可将查询 URL 保存为书签
    - 幂等性：多次调用结果相同
    
    请求示例：
    GET /api/water-quality/history?start_time=2024-01-01T00:00:00&end_time=2024-01-31T23:59:59&sensor_id=sensor-001&page_num=1&page_size=10
    """
    # 模拟数据生成
    mock_data = []
    for i in range(1, page_size + 1):
        mock_item = {
            'id': i,
            'sensor_id': sensor_id or 'sensor-001',
            'pond_id': pond_id or '1',
            'dissolved_oxygen': 6.8 + i * 0.1,
            'ph_value': 7.2 + i * 0.05,
            'temperature': 25.5 + i * 0.1,
            'ammonia_nitrogen': 0.3 + i * 0.01,
            'nitrite': 0.05 + i * 0.005,
            'analysis_result': '水质良好',
            'alert_level': 'normal',
            'created_at': (datetime.now() - timedelta(hours=i)).isoformat()
        }
        mock_data.append(WaterQualityResponse(**mock_item))

    return BaseResponse[WaterQualityHistoryResponse](
        code=200,
        msg="获取成功",
        data=WaterQualityHistoryResponse(
            data=mock_data,
            total=100
        )
    )


class WaterQualityThreshold(BaseModel):
    """水质阈值配置模型"""
    temperature: dict
    ph: dict
    dissolved_oxygen: dict
    ammonia_nitrogen: dict
    nitrite: dict


@router.get("/threshold", response_model=BaseResponse[WaterQualityThreshold])
async def get_water_quality_threshold():
    """异步获取水质阈值配置"""
    return BaseResponse[WaterQualityThreshold](
        code=200,
        msg="获取成功",
        data=WaterQualityThreshold(
            temperature={"min": 20, "max": 28},
            ph={"min": 6.5, "max": 8.5},
            dissolved_oxygen={"min": 5, "max": 15},
            ammonia_nitrogen={"min": 0, "max": 0.5},
            nitrite={"min": 0, "max": 0.1}
        )
    )
