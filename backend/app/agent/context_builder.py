from __future__ import annotations

from hashlib import md5
from typing import Literal

from sqlalchemy.orm import Session

from app.agent.config import get_ai_settings
from app.agent.real_data import get_pond_summary
from app.agent.schemas import (
    AlertSummary,
    BootstrapResponse,
    CurrentPageSummary,
    DeviceStatusSummary,
    MetricSummary,
    PageContextRequest,
    PageContextSummary,
    PondSummary,
    SessionPolicy,
    UICapabilities,
)
from app.agent.tool_registry import (
    get_alert_digest,
    get_allowed_tools,
    get_device_status,
    get_tool_schemas,
    get_water_quality_summary,
)


PAGE_NAMES = {
    "global-chat": "全局 AI 助手",
    "fishery-dashboard": "监测控制台",
    "feeding": "精准投喂",
    "water-quality": "水质监测",
    "growth": "生长识别",
}


def build_page_context(
    request: PageContextRequest, db: Session | None = None
) -> PageContextSummary:
    water = get_water_quality_summary(
        request.pondId, current_index=request.currentIndex, db=db
    )
    pond = get_pond_summary(request.pondId, current_index=request.currentIndex, db=db)
    alert_digest = get_alert_digest(
        request.pondId, current_index=request.currentIndex, db=db
    )
    device_status = get_device_status(
        request.pondId, current_index=request.currentIndex, db=db
    )
    updated_at = water["updatedAt"]
    context_seed = (
        f"{request.pageId}:{request.routePath}:{pond['pondId']}:{updated_at or 'empty'}"
    )
    context_version = md5(context_seed.encode("utf-8")).hexdigest()[:12]

    return PageContextSummary(
        contextVersion=context_version,
        sourceMode=water["sourceMode"],
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
        currentIndex=request.currentIndex,
        updatedAt=updated_at,
    )


def build_system_instructions(
    page_context: PageContextSummary, intent: Literal["qa", "automation"] = "qa"
) -> str:
    mode = get_ai_settings().ai_mode
    page_name = PAGE_NAMES.get(
        page_context.currentPage.pageId, page_context.currentPage.pageId
    )
    intent_instruction = (
        "仅回答用户问题，不执行页面操作。"
        if intent == "qa"
        else "可以调用工具执行页面操作，完成用户的自动化需求。"
    )
    return "\n".join(
        [
            "你是智慧渔业监测系统的 AI 助手。",
            f"当前系统模式：{mode}。",
            '术语规范：统一使用"控制台"称呼当前业务工作区，不使用"驾驶舱"等别名。',
            "请优先用中文直接回答用户，不输出协议字段、JSON 模板或调试痕迹。",
            intent_instruction,
            f"当前页面：{page_name}。",
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
            f"当前池塘：{pond.name}（{pond.pondId}）。",
            f"当前路由：{page_context.currentPage.routePath}。",
            f"上下文版本：{page_context.contextVersion}。",
            f"关键监测指标：{metrics_text or '暂无数据'}。",
            (
                f"告警汇总：总数 {page_context.alertDigest.total}，"
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
    can_execute = page_id == "feeding"
    return UICapabilities(
        canExecute=can_execute,
        canPreview=True,
        showAutomationTab=True,
        showSuggestionPanel=page_id == "feeding",
    )


def build_session_policy() -> SessionPolicy:
    return SessionPolicy(
        persistent=False,
        resumable=False,
        persistenceReserved=True,
    )


def build_bootstrap_payload(
    request: PageContextRequest, intent: Literal["qa", "automation"] = "qa"
) -> BootstrapResponse:
    page_context = build_page_context(request)
    return BootstrapResponse(
        environmentMode=get_ai_settings().ai_mode,
        systemInstructions=build_system_instructions(page_context, intent),
        pageInstructions=build_page_instructions(page_context),
        pageContextSummary=page_context,
        allowedTools=get_allowed_tools(request.pageId),
        toolSchemas=get_tool_schemas(request.pageId),
        uiCapabilities=build_ui_capabilities(request.pageId),
        sessionPolicy=build_session_policy(),
    )
