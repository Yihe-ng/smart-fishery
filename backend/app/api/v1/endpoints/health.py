# backend/app/api/v1/endpoints/health.py
from fastapi import APIRouter
from pydantic import BaseModel
from app.schemas.base import BaseResponse

router = APIRouter()

class HealthOverviewResponse(BaseModel):
    """健康总览响应模型"""
    score: int  # 健康评分 0-100
    risks: dict  # 各种风险等级

@router.get("/overview", response_model=BaseResponse[HealthOverviewResponse])
def get_health_overview():
    """获取健康总览数据"""
    return BaseResponse[HealthOverviewResponse](
        code=200,
        msg="获取成功",
        data=HealthOverviewResponse(
            score=92,
            risks={
                "gillRot": "low",      # 烂鳃风险
                "skinDisease": "medium", # 皮肤病风险
                "enteritis": "low"       # 肠炎风险
            }
        )
    )