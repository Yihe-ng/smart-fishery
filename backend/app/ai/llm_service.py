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
            f"Current mode: {settings.ai_mode}. "
            f"Manual feeding preview generated for pond {target_pond}, amount {amount:.0f}g. "
            "This is a preview only and will not trigger device execution."
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
    settings = get_ai_settings()
    pond_id = _get_pond_id(request)
    last_user_message = next((msg.content for msg in reversed(request.messages) if msg.role == "user"), "")
    lowered = last_user_message.lower()
    warnings = [
        f"Current environment mode is {settings.ai_mode}. Suggestions and previews are for reference only."
    ]

    if "feed" in lowered or "投喂" in last_user_message:
        preview = build_manual_feeding_preview(pond_id, 600)
        return InvokeResponse(
            assistantMessage=(
                "I generated a manual feeding preview based on the current page context. "
                "Review the preview result before taking any real action."
            ),
            toolCalls=[],
            toolResults=None,
            confirmPreview=ConfirmPreview(**preview.model_dump()),
            warnings=warnings,
        )

    if "告警" in last_user_message or "alert" in lowered:
        digest = get_alert_digest(pond_id)
        device = get_device_status(pond_id)
        return InvokeResponse(
            assistantMessage=(
                f"There are {digest['total']} recent alerts, including {digest['critical']} critical and "
                f"{digest['warning']} warning alerts. Devices online: {device['onlineCount']}, "
                f"offline: {device['offlineCount']}."
            ),
            warnings=warnings,
        )

    water = get_water_quality_summary(pond_id)
    feeding = get_feeding_recommendation(pond_id)
    return InvokeResponse(
        assistantMessage=(
            f"{water['overview']} Feeding recommendation: {feeding['recommendation']} "
            f"Latest context update: {water['updatedAt']}."
        ),
        warnings=warnings,
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
        return content

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

    for key in ("response", "answer", "content", "message"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    return content


def _build_real_messages(request: InvokeRequest) -> list[dict[str, str]]:
    pond = request.pageContextSummary.get("pond", {}) if isinstance(request.pageContextSummary, dict) else {}
    current_page = request.pageContextSummary.get("currentPage", {}) if isinstance(request.pageContextSummary, dict) else {}
    metrics = request.pageContextSummary.get("keyMetrics", []) if isinstance(request.pageContextSummary, dict) else []
    alerts = request.pageContextSummary.get("alertDigest", {}) if isinstance(request.pageContextSummary, dict) else {}
    devices = request.pageContextSummary.get("deviceStatus", {}) if isinstance(request.pageContextSummary, dict) else {}
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

    latest_user_message = next((message.content for message in reversed(request.messages) if message.role == "user"), "")

    return [
        {
            "role": "system",
            "content": (
                "You are an AI assistant for a smart fishery monitoring system. "
                "Answer the user directly in Chinese. "
                "Do not return JSON, Markdown code fences, planning traces, memory fields, or tool protocol text. "
                "If the user asks a simple greeting, respond naturally in one short paragraph. "
                "If the user asks for advice, base the answer on the provided context and keep it concise."
            ),
        },
        {
            "role": "system",
            "content": f"Current page context:\n{context_text}",
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
            assistantMessage="LLM request failed. Falling back to an error response.",
            warnings=[f"HTTP {exc.code}", detail[:500] or "No response body returned by upstream model service."],
        )
    except urllib.error.URLError as exc:
        return InvokeResponse(
            assistantMessage="LLM request failed. Falling back to an error response.",
            warnings=[f"Network error: {exc.reason}"],
        )
    except Exception as exc:
        return InvokeResponse(
            assistantMessage="Unexpected model invocation error.",
            warnings=[str(exc)],
        )

    content = raw_payload.get("choices", [{}])[0].get("message", {}).get("content")
    if not content:
        content = "Model service returned an empty response."
    else:
        content = _extract_display_text(content)

    return InvokeResponse(
        assistantMessage=content,
        warnings=["Response generated by upstream model service."],
    )
