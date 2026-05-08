from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from app.agent.config import get_ai_settings
from app.agent.preview_store import save_manual_feeding_preview_snapshot
from app.agent.schemas import (
    ConfirmPreview,
    InvokeRequest,
    InvokeResponse,
    ManualFeedingPreviewResponse,
    ToolCall,
)
from app.agent.tool_registry import (
    PAGE_TOOL_WHITELIST,
    TOOL_DEFINITIONS,
    get_alert_digest,
    get_device_status,
    get_feeding_recommendation,
    get_water_quality_summary,
    run_tool,
)

MAX_TOOL_CALLS = 2


def build_manual_feeding_preview(
    pond_id: str | None, amount: float
) -> ManualFeedingPreviewResponse:
    settings = get_ai_settings()
    target_pond = pond_id or "pond-001"
    feeder_id = "feeder-001"
    duration = 10
    expires_at = (datetime.now() + timedelta(minutes=10)).isoformat()
    confirm_token = f"preview-{uuid4().hex[:16]}"
    save_manual_feeding_preview_snapshot(
        confirm_token=confirm_token,
        pond_id=target_pond,
        feeder_id=feeder_id,
        amount=amount,
        duration=duration,
        expires_at=expires_at,
    )
    return ManualFeedingPreviewResponse(
        actionType="manual_feeding_preview",
        previewText=(
            f"已生成手动投喂预览：池塘 {target_pond}，投喂量 {amount:.0f}g。"
            "该结果仅为预览，需确认后才会执行。"
        ),
        riskLevel="warning",
        confirmToken=confirm_token,
        pondId=target_pond,
        feederId=feeder_id,
        amount=amount,
        duration=duration,
        expiresAt=expires_at,
        mode=settings.ai_mode,
    )


def _get_pond_id(request: InvokeRequest) -> str | None:
    pond = request.pageContextSummary.get("pond")
    if isinstance(pond, dict):
        return pond.get("pondId")
    return None


def _get_current_index(request: InvokeRequest) -> int | None:
    value = request.pageContextSummary.get("currentIndex")
    return value if isinstance(value, int) else None


def _latest_user_message(request: InvokeRequest) -> str:
    return next(
        (msg.content for msg in reversed(request.messages) if msg.role == "user"), ""
    )


def _extract_amount(text: str) -> float:
    match = re.search(r"(\d+(?:\.\d+)?)\s*g", text, flags=re.IGNORECASE)
    if match:
        return float(match.group(1))
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    if match:
        return float(match.group(1))
    return 600.0


def _mock_decide_next_step(
    request: InvokeRequest,
    allowed_tools: list[str],
    tool_results: list[dict[str, Any]],
) -> dict[str, Any]:
    message = _latest_user_message(request)
    lowered = message.lower()
    pond_id = _get_pond_id(request)
    current_index = _get_current_index(request)

    if tool_results:
        last_result = tool_results[-1]
        tool = last_result["tool"]
        output = last_result["output"]
        if tool == "preview_manual_feeding_action":
            return {
                "type": "answer",
                "assistantMessage": "我已经根据当前快照生成手动投喂预览，请确认后再执行。",
                "confirmPreview": output,
            }
        if tool == "get_water_quality_summary":
            return {
                "type": "answer",
                "assistantMessage": f"{output['overview']} 数据更新时间：{output['updatedAt'] or '暂无'}。",
            }
        if tool == "get_device_status":
            return {
                "type": "answer",
                "assistantMessage": (
                    f"当前设备在线 {output['onlineCount']} 台，离线 {output['offlineCount']} 台，"
                    f"投喂机状态 {output['feederStatus']}，摄像头状态 {output['cameraStatus']}。"
                ),
            }
        if tool == "get_alert_digest":
            latest = output.get("latest", [])
            latest_text = latest[0]["title"] if latest else "暂无最新告警"
            return {
                "type": "answer",
                "assistantMessage": (
                    f"当前共有 {output['total']} 条告警，其中严重 {output['critical']} 条，"
                    f"警告 {output['warning']} 条，最近告警：{latest_text}。"
                ),
            }
        if tool == "get_feeding_recommendation":
            return {
                "type": "answer",
                "assistantMessage": output["recommendation"],
            }
        return {
            "type": "answer",
            "assistantMessage": "工具已经执行，但当前无法进一步整理结果。",
        }

    if ("预览" in message or "preview" in lowered) and (
        "投喂" in message or "feed" in lowered or "feeding" in lowered
    ):
        return {
            "type": "tool",
            "toolName": "preview_manual_feeding_action",
            "arguments": {
                "pondId": pond_id,
                "currentIndex": current_index,
                "amount": _extract_amount(message),
            },
        }
    if "设备" in message or "device" in lowered:
        return {
            "type": "tool",
            "toolName": "get_device_status",
            "arguments": {"pondId": pond_id, "currentIndex": current_index},
        }
    if "告警" in message or "alert" in lowered:
        return {
            "type": "tool",
            "toolName": "get_alert_digest",
            "arguments": {"pondId": pond_id, "currentIndex": current_index},
        }
    if "建议" in message or "投喂" in message or "feeding" in lowered:
        return {
            "type": "tool",
            "toolName": "get_feeding_recommendation",
            "arguments": {"pondId": pond_id, "currentIndex": current_index},
        }
    if "水质" in message or "water" in lowered:
        return {
            "type": "tool",
            "toolName": "get_water_quality_summary",
            "arguments": {"pondId": pond_id, "currentIndex": current_index},
        }

    water = get_water_quality_summary(pond_id, current_index=current_index)
    return {
        "type": "answer",
        "assistantMessage": f"{water['overview']} 如果你愿意，我也可以继续帮你查看告警、设备或投喂建议。",
    }


def _build_remote_messages(
    request: InvokeRequest,
    allowed_tools: list[str],
    tool_results: list[dict[str, Any]],
) -> list[dict[str, str]]:
    tool_descriptions = [
        {"name": name, "description": TOOL_DEFINITIONS[name]["description"]}
        for name in allowed_tools
        if name in TOOL_DEFINITIONS
    ]
    ctx_text = json.dumps(request.pageContextSummary, ensure_ascii=False)
    latest_user = _latest_user_message(request)
    tool_results_text = json.dumps(tool_results, ensure_ascii=False)
    system_prompt = (
        "你是智慧渔业系统的后端助手。"
        "你必须只返回 JSON，不要输出任何额外文本。"
        '如果需要调用工具，请返回：{"type":"tool","toolName":"工具名","arguments":{"pondId":"...","currentIndex":1}}。'
        '如果已经可以直接回答，请返回：{"type":"answer","assistantMessage":"给用户的中文回答"}。'
        "只允许使用提供的工具，不要虚构工具。"
    )
    return [
        {"role": "system", "content": system_prompt},
        {
            "role": "system",
            "content": f"当前页面上下文：{ctx_text}\n允许工具：{json.dumps(tool_descriptions, ensure_ascii=False)}",
        },
        {"role": "system", "content": f"已执行工具结果：{tool_results_text}"},
        {"role": "user", "content": latest_user},
    ]


def _extract_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        lines = lines[1:-1] if len(lines) >= 2 else lines
        stripped = "\n".join(lines).strip()
    try:
        payload = json.loads(stripped)
        if isinstance(payload, dict):
            return payload
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{[\s\S]*\}", stripped)
    if not match:
        raise ValueError("model returned invalid JSON")
    payload = json.loads(match.group(0))
    if not isinstance(payload, dict):
        raise ValueError("model JSON payload is not an object")
    return payload


def _remote_decide_next_step(
    request: InvokeRequest,
    allowed_tools: list[str],
    tool_results: list[dict[str, Any]],
) -> dict[str, Any]:
    settings = get_ai_settings()
    payload = {
        "model": settings.ai_model,
        "messages": _build_remote_messages(request, allowed_tools, tool_results),
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
        return {
            "type": "answer",
            "assistantMessage": f"远程模型服务返回错误（HTTP {exc.code}），已切换到降级模式。",
        }
    except urllib.error.URLError as exc:
        return {
            "type": "answer",
            "assistantMessage": f"无法连接远程模型服务（{exc.reason}），已切换到降级模式。",
        }
    except TimeoutError:
        return {
            "type": "answer",
            "assistantMessage": "远程模型服务响应超时，已切换到降级模式。",
        }
    content = raw_payload.get("choices", [{}])[0].get("message", {}).get("content", "")
    if not content:
        return {
            "type": "answer",
            "assistantMessage": "远程模型返回空响应，已切换到降级模式。",
        }
    try:
        return _extract_json_object(content)
    except ValueError:
        return {
            "type": "answer",
            "assistantMessage": "远程模型返回格式异常，已切换到降级模式。",
        }


def _decide_next_step(
    request: InvokeRequest,
    allowed_tools: list[str],
    tool_results: list[dict[str, Any]],
) -> dict[str, Any]:
    settings = get_ai_settings()
    if settings.ai_mode == "mock" or not settings.agent_sk:
        return _mock_decide_next_step(request, allowed_tools, tool_results)
    return _remote_decide_next_step(request, allowed_tools, tool_results)


def _normalize_allowed_tools(request: InvokeRequest) -> list[str]:
    page_whitelist = PAGE_TOOL_WHITELIST.get(
        request.pageId, PAGE_TOOL_WHITELIST["global-chat"]
    )
    requested = request.allowedTools or page_whitelist
    return [tool for tool in requested if tool in page_whitelist]


def _execute_tool(
    request: InvokeRequest, tool_name: str, arguments: dict[str, Any]
) -> dict[str, Any]:
    if tool_name == "preview_manual_feeding_action":
        preview = build_manual_feeding_preview(
            arguments.get("pondId") or _get_pond_id(request),
            float(arguments.get("amount", 600)),
        )
        return preview.model_dump()

    normalized = dict(arguments)
    if "pondId" not in normalized and _get_pond_id(request) is not None:
        normalized["pondId"] = _get_pond_id(request)
    if "currentIndex" not in normalized and _get_current_index(request) is not None:
        normalized["currentIndex"] = _get_current_index(request)
    return run_tool(tool_name, **normalized)


def _build_response(
    *,
    status: str,
    assistant_message: str,
    tool_calls: list[ToolCall],
    tool_results: list[dict[str, Any]],
    warnings: list[str],
    confirm_preview: ConfirmPreview | None = None,
) -> InvokeResponse:
    return InvokeResponse(
        status=status,
        assistantMessage=assistant_message,
        toolCalls=tool_calls,
        toolResults=tool_results or None,
        confirmPreview=confirm_preview,
        warnings=warnings,
        messageId=f"msg_{uuid4().hex[:12]}",
    )


def invoke_llm(request: InvokeRequest) -> InvokeResponse:
    allowed_tools = _normalize_allowed_tools(request)
    warnings: list[str] = []
    tool_calls: list[ToolCall] = []
    tool_results: list[dict[str, Any]] = []
    confirm_preview: ConfirmPreview | None = None
    assistant_message = ""
    status = "completed"

    for _ in range(MAX_TOOL_CALLS + 1):
        try:
            decision = _decide_next_step(request, allowed_tools, tool_results)
        except urllib.error.HTTPError as exc:
            warnings.append(f"Model HTTP error: {exc.code}")
            decision = _mock_decide_next_step(request, allowed_tools, tool_results)
        except urllib.error.URLError as exc:
            warnings.append(f"Model network error: {exc.reason}")
            decision = _mock_decide_next_step(request, allowed_tools, tool_results)
        except Exception as exc:
            warnings.append(f"Model response invalid: {exc}")
            decision = _mock_decide_next_step(request, allowed_tools, tool_results)

        if decision.get("type") == "answer":
            assistant_message = (
                decision.get("assistantMessage", "").strip() or "当前暂无可展示结果。"
            )
            preview_payload = decision.get("confirmPreview")
            if isinstance(preview_payload, dict):
                confirm_preview = ConfirmPreview(**preview_payload)
                if status == "completed":
                    status = "requires_confirmation"
            return _build_response(
                status=status,
                assistant_message=assistant_message,
                tool_calls=tool_calls,
                tool_results=tool_results,
                warnings=warnings,
                confirm_preview=confirm_preview,
            )

        if decision.get("type") != "tool":
            warnings.append("Model returned no valid action")
            return _build_response(
                status="degraded",
                assistant_message="模型没有返回有效的工具调用或最终回答，请换个问法再试一次。",
                tool_calls=tool_calls,
                tool_results=tool_results,
                warnings=warnings,
                confirm_preview=confirm_preview,
            )

        tool_name = decision.get("toolName")
        arguments = decision.get("arguments", {})
        if not isinstance(tool_name, str) or tool_name not in TOOL_DEFINITIONS:
            warnings.append("Requested tool does not exist")
            return _build_response(
                status="degraded",
                assistant_message="请求的工具不存在，当前无法继续处理。",
                tool_calls=tool_calls,
                tool_results=tool_results,
                warnings=warnings,
                confirm_preview=confirm_preview,
            )
        if tool_name not in allowed_tools:
            warnings.append(f"Tool not allowed: {tool_name}")
            return _build_response(
                status="degraded",
                assistant_message="该请求涉及当前页面未授权的工具，已停止执行。",
                tool_calls=tool_calls,
                tool_results=tool_results,
                warnings=warnings,
                confirm_preview=confirm_preview,
            )
        if len(tool_calls) >= MAX_TOOL_CALLS:
            warnings.append("Tool call limit exceeded")
            return _build_response(
                status="degraded",
                assistant_message="本次请求需要的工具调用超过上限，我已停止继续编排。",
                tool_calls=tool_calls,
                tool_results=tool_results,
                warnings=warnings,
                confirm_preview=confirm_preview,
            )

        if not isinstance(arguments, dict):
            arguments = {}
        tool_calls.append(ToolCall(name=tool_name, arguments=arguments))
        try:
            output = _execute_tool(request, tool_name, arguments)
        except Exception as exc:
            warnings.append(f"Tool execution failed: {tool_name}")
            return _build_response(
                status="degraded",
                assistant_message=f"工具 {tool_name} 执行失败，请稍后重试。",
                tool_calls=tool_calls,
                tool_results=tool_results,
                warnings=warnings + [str(exc)],
                confirm_preview=confirm_preview,
            )
        tool_results.append(
            {"tool": tool_name, "arguments": arguments, "output": output, "ok": True}
        )
        if tool_name == "preview_manual_feeding_action":
            confirm_preview = ConfirmPreview(**output)

    warnings.append("Tool loop ended without final answer")
    return _build_response(
        status="degraded",
        assistant_message="本次请求未能在受限工具编排内完成，我已停止继续尝试。",
        tool_calls=tool_calls,
        tool_results=tool_results,
        warnings=warnings,
        confirm_preview=confirm_preview,
    )
