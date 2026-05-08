import asyncio

from app.agent.config import get_ai_settings
from app.agent.schemas import SuggestionCard, SuggestionPanelState, SuggestionResponse
from app.agent.tool_registry import (
    get_alert_digest,
    get_device_status,
    get_feeding_recommendation,
    get_water_quality_summary,
)


def _normalize_severity(value: str | None) -> str:
    return value if value in {"info", "warning", "critical"} else "info"


def _build_risk_summary(alerts: dict, devices: dict) -> tuple[str, list[str], str]:
    critical = alerts.get("critical", 0)
    warning = alerts.get("warning", 0)
    online = devices.get("onlineCount", 0)
    offline = devices.get("offlineCount", 0)
    latest = alerts.get("latest", [])
    reasons = [
        f"当前严重告警 {critical} 条，警告 {warning} 条。",
        f"设备在线 {online} 台，离线 {offline} 台。",
    ]
    if latest:
        reasons.append(f"最近告警：{latest[0].get('title', '暂无详情')}")
    severity = "critical" if critical > 0 else "warning" if warning > 0 or offline > 0 else "info"
    summary = (
        "当前快照存在需要关注的风险。"
        if severity != "info"
        else "当前快照下未发现明显设备或告警风险。"
    )
    return summary, reasons, severity


async def build_feeding_suggestions(
    pond_id: str | None = None, current_index: int | None = None
) -> SuggestionResponse:
    mode = get_ai_settings().ai_mode
    water = get_water_quality_summary(pond_id, current_index=current_index)
    recommendation = get_feeding_recommendation(pond_id, current_index=current_index)
    alerts = get_alert_digest(pond_id, current_index=current_index)
    devices = get_device_status(pond_id, current_index=current_index)

    cards: list[SuggestionCard] = []
    if recommendation.get("canFeed", False):
        cards.append(
            SuggestionCard(
                id="feeding-recommendation",
                title="当前投喂建议",
                summary=recommendation.get("recommendation", "当前快照下暂无明确投喂建议。"),
                rationale=recommendation.get("rationale", []),
                confidence=float(recommendation.get("confidence", 0.6)),
                severity=_normalize_severity(water.get("riskLevel")),
                sourceMode=recommendation.get("sourceMode", mode),
                updatedAt=water.get("updatedAt"),
                suggestedAction="查看投喂预览",
                confirmRequired=True,
                suggestedAmount=recommendation.get("recommendedAmount"),
            )
        )
    else:
        cards.append(
            SuggestionCard(
                id="feeding-recommendation-unavailable",
                title="当前投喂建议",
                summary=recommendation.get("recommendation", "当前快照下暂不建议投喂。"),
                rationale=recommendation.get("rationale", []),
                confidence=float(recommendation.get("confidence", 0.55)),
                severity=_normalize_severity(water.get("riskLevel") or "warning"),
                sourceMode=recommendation.get("sourceMode", mode),
                updatedAt=water.get("updatedAt"),
                suggestedAction="继续查看 AI 助手",
                confirmRequired=False,
            )
        )

    risk_summary, risk_rationale, risk_severity = _build_risk_summary(alerts, devices)
    cards.append(
        SuggestionCard(
            id="feeding-risk-summary",
            title="当前风险摘要",
            summary=risk_summary,
            rationale=risk_rationale,
            confidence=0.7 if risk_severity != "info" else 0.8,
            severity=risk_severity,
            sourceMode=mode,
            updatedAt=water.get("updatedAt"),
            suggestedAction="查看 AI 助手分析",
            confirmRequired=False,
        )
    )

    return SuggestionResponse(
        cards=cards,
        panelState=SuggestionPanelState(
            hasNewRisk=risk_severity != "info",
            hasNewSuggestion=bool(cards),
        ),
    )


def build_feeding_suggestions_sync(
    pond_id: str | None = None, current_index: int | None = None
) -> SuggestionResponse:
    return asyncio.run(build_feeding_suggestions(pond_id, current_index))
