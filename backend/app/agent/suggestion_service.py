import asyncio

from app.agent.config import get_ai_settings
from app.agent.mock_data import get_mock_feeding_logs
from app.agent.schemas import SuggestionCard, SuggestionPanelState, SuggestionResponse
from app.agent.tool_registry import (
    get_alert_digest,
    get_feeding_recommendation,
    get_water_quality_summary,
)


async def build_feeding_suggestions(pond_id: str | None = None) -> SuggestionResponse:
    mode = get_ai_settings().ai_mode
    water = get_water_quality_summary(pond_id)
    recommendation = await get_feeding_recommendation(pond_id)
    alerts = get_alert_digest(pond_id)
    latest_log = get_mock_feeding_logs(1)[0]

    # 根据气压风险等级计算建议投喂量
    pressure_risk = recommendation.get("pressureRisk", {})
    risk_level = pressure_risk.get("level", "low")
    base_amount = 550  # 基础建议投喂量

    if risk_level == "high":
        suggested_amount = int(base_amount * 0.5)  # 高风险减少50%
    elif risk_level == "medium":
        suggested_amount = int(base_amount * 0.8)  # 中风险减少20%
    else:
        suggested_amount = base_amount  # 低风险正常投喂

    cards = [
        SuggestionCard(
            id="feeding-risk-summary",
            title="投喂建议保持保守",
            summary=recommendation["recommendation"],
            rationale=recommendation["rationale"],
            confidence=recommendation["confidence"],
            severity="warning" if risk_level != "low" else "info",
            sourceMode=mode,
            updatedAt=water["updatedAt"],
            suggestedAction="查看投喂预览",
            confirmRequired=True,
            suggestedAmount=suggested_amount,
        ),
        SuggestionCard(
            id="feeding-alert-check",
            title="先处理设备与告警风险",
            summary=f"当前有 {alerts['critical']} 条严重告警、{alerts['warning']} 条警告，建议先确认传感器与设备状态。",
            rationale=[
                "亚硝酸盐传感器离线会降低建议可信度。",
                f"最近一次投喂记录为 {latest_log['feedTime']}，投喂量 {latest_log['amount']}g。",
            ],
            confidence=0.69,
            severity="warning" if alerts["critical"] == 0 else "critical",
            sourceMode=mode,
            updatedAt=water["updatedAt"],
            suggestedAction="查看异常汇总",
            confirmRequired=False,
        ),
    ]
    return SuggestionResponse(
        cards=cards,
        panelState=SuggestionPanelState(hasNewRisk=True, hasNewSuggestion=True),
    )


# 为了保持向后兼容，提供同步版本
def build_feeding_suggestions_sync(pond_id: str | None = None) -> SuggestionResponse:
    """同步版本的投喂建议生成（用于兼容旧代码）"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果事件循环已经在运行，创建新任务
            return asyncio.create_task(build_feeding_suggestions(pond_id))
        else:
            return loop.run_until_complete(build_feeding_suggestions(pond_id))
    except RuntimeError:
        # 没有事件循环时创建新的
        return asyncio.run(build_feeding_suggestions(pond_id))
