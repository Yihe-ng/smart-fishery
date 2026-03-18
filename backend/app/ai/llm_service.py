import json
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from uuid import uuid4

from app.ai.config import get_ai_settings
from app.ai.schemas import ConfirmPreview, InvokeRequest, InvokeResponse, ManualFeedingPreviewResponse
from app.ai.tool_registry import (
    get_alert_digest,
    get_device_status,
    get_feeding_recommendation,
    get_water_quality_summary,
)


def build_manual_feeding_preview(pond_id: str | None, amount: float) -> ManualFeedingPreviewResponse:
    settings = get_ai_settings()
    target_pond = pond_id or "pond-001"
    expires_at = (datetime.now() + timedelta(minutes=10)).isoformat()
    return ManualFeedingPreviewResponse(
        actionType="manual_feeding_preview",
        previewText=(
            f"已生成手动投喂预览：池塘 {target_pond}，投喂量 {amount:.0f}g。"
            "该结果仅为预览，需在前端确认后才会执行。"
        ),
        riskLevel="warning",
        confirmToken=f"preview-{uuid4().hex[:16]}",
        expiresAt=expires_at,
        mode=settings.ai_mode,
    )


def _get_pond_id(request: InvokeRequest) -> str | None:
    pond = request.pageContextSummary.get("pond")
    if isinstance(pond, dict):
        return pond.get("pondId")
    return None


def _build_mock_response(request: InvokeRequest) -> InvokeResponse:
    pond_id = _get_pond_id(request)
    last_user_message = next((msg.content for msg in reversed(request.messages) if msg.role == "user"), "")
    lowered = last_user_message.lower()

    if "feed" in lowered or "投喂" in last_user_message:
        preview = build_manual_feeding_preview(pond_id, 600)
        return InvokeResponse(
            assistantMessage="我已基于当前页面数据生成投喂预览，请确认后执行。",
            toolCalls=[],
            toolResults=None,
            confirmPreview=ConfirmPreview(**preview.model_dump()),
            warnings=[],
        )

    if "告警" in last_user_message or "alert" in lowered:
        digest = get_alert_digest(pond_id)
        device = get_device_status(pond_id)
        return InvokeResponse(
            assistantMessage=(
                f"当前共有 {digest['total']} 条告警，其中严重 {digest['critical']} 条、"
                f"警告 {digest['warning']} 条。设备在线 {device['onlineCount']} 台，"
                f"离线 {device['offlineCount']} 台。"
            ),
            warnings=[],
        )

    water = get_water_quality_summary(pond_id)
    feeding = get_feeding_recommendation(pond_id)
    return InvokeResponse(
        assistantMessage=(
            f"{water['overview']} 当前投喂建议：{feeding['recommendation']}。"
            f"数据更新时间：{water['updatedAt']}。"
        ),
        warnings=[],
    )


def _strip_code_fence(content: str) -> str:
    text = content.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def _extract_display_text(content: str) -> str:
    text = _strip_code_fence(content)

    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return text

    action = payload.get("action")
    if isinstance(action, dict):
        done = action.get("done")
        if isinstance(done, dict):
            done_text = done.get("text")
            if isinstance(done_text, str) and done_text.strip():
                return done_text.strip()

        action_text = action.get("text")
        if isinstance(action_text, str) and action_text.strip():
            return action_text.strip()

    for key in ("response", "answer", "content", "message", "text"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    return text


def _build_real_messages(request: InvokeRequest) -> list[dict[str, str]]:
    pond = request.pageContextSummary.get("pond", {}) if isinstance(request.pageContextSummary, dict) else {}
    current_page = (
        request.pageContextSummary.get("currentPage", {})
        if isinstance(request.pageContextSummary, dict)
        else {}
    )
    metrics = request.pageContextSummary.get("keyMetrics", []) if isinstance(request.pageContextSummary, dict) else []
    alerts = request.pageContextSummary.get("alertDigest", {}) if isinstance(request.pageContextSummary, dict) else {}
    devices = (
        request.pageContextSummary.get("deviceStatus", {})
        if isinstance(request.pageContextSummary, dict)
        else {}
    )
    updated_at = request.pageContextSummary.get("updatedAt", "") if isinstance(request.pageContextSummary, dict) else ""

    metrics_text = ", ".join(
        [
            f"{item.get('label', item.get('key', 'metric'))}: {item.get('value', '')}{item.get('unit', '')} ({item.get('status', '')})"
            for item in metrics
            if isinstance(item, dict)
        ]
    )

    context_text = (
        f"page_id={request.pageId}\n"
        f"route_path={current_page.get('routePath', '')}\n"
        f"pond_id={pond.get('pondId', '')}\n"
        f"pond_name={pond.get('name', '')}\n"
        f"source_mode={request.pageContextSummary.get('sourceMode', '')}\n"
        f"context_version={request.contextVersion}\n"
        f"updated_at={updated_at}\n"
        f"metrics={metrics_text}\n"
        f"alerts_total={alerts.get('total', 0)} critical={alerts.get('critical', 0)} warning={alerts.get('warning', 0)}\n"
        f"devices_online={devices.get('onlineCount', 0)} offline={devices.get('offlineCount', 0)}"
    )

    latest_user_message = next(
        (message.content for message in reversed(request.messages) if message.role == "user"),
        "",
    )

    return [
        {
            "role": "system",
            "content": (
                "你是智慧渔业系统助手，请直接用简洁中文回答。"
                "不要返回 JSON、代码块、协议字段、规划痕迹或 memory/next_goal 等内部字段。"
            ),
        },
        {
            "role": "system",
            "content": f"当前页面上下文：\n{context_text}",
        },
        {
            "role": "user",
            "content": latest_user_message,
        },
    ]


def invoke_llm(request: InvokeRequest) -> InvokeResponse:
    settings = get_ai_settings()

    if settings.ai_mode == "mock" or not settings.agent_sk:
        return _build_mock_response(request)

    payload = {
        "model": settings.ai_model,
        "messages": _build_real_messages(request),
    }
    http_request = urllib.request.Request(
        settings.ai_base_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.agent_sk}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(http_request, timeout=20) as response:
            raw_payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        return InvokeResponse(
            assistantMessage="模型服务请求失败，请稍后重试。",
            warnings=[f"HTTP {exc.code}", detail[:500] or "上游模型服务未返回详细信息。"],
        )
    except urllib.error.URLError as exc:
        return InvokeResponse(
            assistantMessage="模型服务网络异常，请稍后重试。",
            warnings=[f"网络错误: {exc.reason}"],
        )
    except Exception as exc:
        return InvokeResponse(
            assistantMessage="模型调用出现异常，请稍后重试。",
            warnings=[str(exc)],
        )

    content = raw_payload.get("choices", [{}])[0].get("message", {}).get("content")
    if not content:
        content = "模型服务暂未返回有效内容。"
    else:
        content = _extract_display_text(content)

    return InvokeResponse(
        assistantMessage=content,
        warnings=[],
    )
