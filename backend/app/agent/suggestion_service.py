from app.agent.config import get_ai_settings
from app.agent.mock_data import get_mock_feeding_logs
from app.agent.schemas import SuggestionCard, SuggestionPanelState, SuggestionResponse
from app.agent.tool_registry import (
    get_alert_digest,
    get_feeding_recommendation,
    get_water_quality_summary,
)


def build_feeding_suggestions(pond_id: str | None = None) -> SuggestionResponse:
    mode = get_ai_settings().ai_mode
    water = get_water_quality_summary(pond_id)
    recommendation = get_feeding_recommendation(pond_id)
    alerts = get_alert_digest(pond_id)
    latest_log = get_mock_feeding_logs(1)[0]
    cards = [
        SuggestionCard(
            id="feeding-risk-summary",
            title="投喂建议保持保守",
            summary=recommendation["recommendation"],
            rationale=recommendation["rationale"],
            confidence=recommendation["confidence"],
            severity="warning",
            sourceMode=mode,
            updatedAt=water["updatedAt"],
            suggestedAction="查看投喂预览",
            confirmRequired=True,
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
