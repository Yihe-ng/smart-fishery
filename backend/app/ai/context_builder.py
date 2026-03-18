from hashlib import md5
from typing import Dict

from app.ai.config import get_ai_settings
from app.ai.mock_data import get_mock_pond, get_mock_water_quality
from app.ai.schemas import (
    AlertSummary,
    CurrentPageSummary,
    DeviceStatusSummary,
    MetricSummary,
    PageContextRequest,
    PageContextSummary,
    PondSummary,
    SessionPolicy,
    UICapabilities,
)
from app.ai.tool_registry import get_alert_digest, get_allowed_tools, get_device_status


PAGE_NAMES = {
    "global-chat": "全局 AI 助手",
    "fishery-dashboard": "监测大屏",
    "feeding": "精准投喂",
    "water-quality": "水质监测",
    "growth": "生长识别",
}


def build_page_context(request: PageContextRequest) -> PageContextSummary:
    mode = get_ai_settings().ai_mode
    water = get_mock_water_quality(request.pondId)
    pond = get_mock_pond(request.pondId)
    alert_digest = get_alert_digest(request.pondId)
    device_status = get_device_status(request.pondId)
    updated_at = water["updatedAt"]
    context_seed = f"{request.pageId}:{request.routePath}:{pond['pondId']}:{updated_at}"
    context_version = md5(context_seed.encode("utf-8")).hexdigest()[:12]

    return PageContextSummary(
        contextVersion=context_version,
        sourceMode=mode,
        currentPage=CurrentPageSummary(
            pageId=request.pageId,
            routePath=request.routePath,
            selection=request.selection or {},
        ),
        pond=PondSummary(**pond),
        keyMetrics=[MetricSummary(**metric) for metric in water["metrics"]],
        alertDigest=AlertSummary(
            total=alert_digest["total"],
            critical=alert_digest["critical"],
            warning=alert_digest["warning"],
            latestTitles=[item["title"] for item in alert_digest["latest"]],
        ),
        deviceStatus=DeviceStatusSummary(**device_status),
        updatedAt=updated_at,
    )


def build_system_instructions(page_context: PageContextSummary) -> str:
    mode = get_ai_settings().ai_mode
    page_name = PAGE_NAMES.get(page_context.currentPage.pageId, page_context.currentPage.pageId)
    return "\n".join(
        [
            "你是石斑鱼智慧监测系统的 AI 助手。",
            f"当前运行模式为 {mode}。",
            "请根据页面上下文直接回答用户，不要输出 JSON、协议字段、推理轨迹、memory、next_goal、action 等结构化内容。",
            "回答要简洁、自然、面向业务用户。",
            "如果涉及控制、执行、投喂等高风险动作，只能给建议或预览，不能宣称已经真实执行。",
            f"当前页面是：{page_name}。",
        ]
    )


def build_page_instructions(page_context: PageContextSummary) -> str:
    pond = page_context.pond
    metrics_text = "；".join(
        [
            f"{metric.label} {metric.value}{metric.unit}（{metric.status}）"
            for metric in page_context.keyMetrics
        ]
    )
    return "\n".join(
        [
            f"当前鱼塘：{pond.name}（{pond.pondId}）。",
            f"当前路由：{page_context.currentPage.routePath}。",
            f"上下文版本：{page_context.contextVersion}。",
            f"关键监测指标：{metrics_text}。",
            (
                f"告警摘要：总数 {page_context.alertDigest.total}，"
                f"严重 {page_context.alertDigest.critical}，"
                f"警告 {page_context.alertDigest.warning}。"
            ),
            (
                f"设备状态：在线 {page_context.deviceStatus.onlineCount}，"
                f"离线 {page_context.deviceStatus.offlineCount}。"
            ),
        ]
    )


def build_ui_capabilities(page_id: str) -> UICapabilities:
    return UICapabilities(
        canExecute=False,
        showAutomationTab=True,
        showSuggestionPanel=page_id == "feeding",
    )


def build_session_policy() -> SessionPolicy:
    return SessionPolicy(
        persistent=False,
        resumable=False,
        persistenceReserved=True,
    )


def build_bootstrap_payload(request: PageContextRequest) -> Dict[str, object]:
    mode = get_ai_settings().ai_mode
    page_context = build_page_context(request)
    return {
        "environmentMode": mode,
        "systemInstructions": build_system_instructions(page_context),
        "pageInstructions": build_page_instructions(page_context),
        "pageContextSummary": page_context,
        "allowedTools": get_allowed_tools(request.pageId),
        "uiCapabilities": build_ui_capabilities(request.pageId),
        "sessionPolicy": build_session_policy(),
    }
