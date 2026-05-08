from __future__ import annotations

from typing import Any, Callable, Dict, List

from sqlalchemy.orm import Session

from app.agent.real_data import (
    get_alert_digest_data,
    get_device_status_data,
    get_water_quality_snapshot,
    get_water_quality_summary_data,
)
from app.services.smart_feeding import smart_feeding_service
from app.services.weather_service import weather_service


def get_water_quality_summary(
    pond_id: str | None = None,
    current_index: int | None = None,
    db: Session | None = None,
) -> Dict[str, Any]:
    return get_water_quality_summary_data(pond_id, current_index=current_index, db=db)


def get_feeding_recommendation(
    pond_id: str | None = None,
    current_index: int | None = None,
    db: Session | None = None,
) -> Dict[str, Any]:
    water_snapshot = get_water_quality_snapshot(
        pond_id, current_index=current_index, db=db
    )
    pressure_risk = weather_service.get_pressure_risk_for_feeding(None)
    plan = smart_feeding_service.calculate_feeding_plan(
        pond_id=pond_id or "pond-001",
        current_index=current_index,
        db=db,
    )

    if not plan["can_feed"]:
        return {
            "canFeed": False,
            "recommendation": plan.get("reason") or plan.get("suggestion", "暂不建议投喂。"),
            "confidence": 0.55,
            "factors": {},
            "rationale": [plan.get("reason", "缺少实时水质数据，无法给出投喂建议。")],
            "sourceMode": "real",
            "pressureRisk": pressure_risk,
            "waterQuality": water_snapshot or {},
        }

    rationale = [
        f"当前溶解氧 {plan['water_quality']['dissolved_oxygen']}mg/L。",
        f"当前水温 {plan['water_quality']['temperature']}°C。",
        f"推荐投喂量约 {plan['recommended_amount']}g，建议时段 {plan['optimal_time']}。",
    ]
    return {
        "canFeed": True,
        "recommendation": plan["suggestion"],
        "confidence": plan["confidence"],
        "factors": plan["factors"],
        "rationale": rationale,
        "sourceMode": "real",
        "pressureRisk": pressure_risk,
        "waterQuality": plan["water_quality"],
        "recommendedAmount": plan["recommended_amount"],
        "estimatedDuration": plan["estimated_duration"],
    }


def get_alert_digest(
    pond_id: str | None = None,
    limit: int = 3,
    current_index: int | None = None,
    db: Session | None = None,
) -> Dict[str, Any]:
    return get_alert_digest_data(
        pond_id, limit=limit, current_index=current_index, db=db
    )


def get_device_status(
    pond_id: str | None = None,
    current_index: int | None = None,
    db: Session | None = None,
) -> Dict[str, Any]:
    return get_device_status_data(pond_id, current_index=current_index, db=db)


ToolHandler = Callable[..., Dict[str, Any]]


TOOL_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "get_water_quality_summary": {
        "name": "get_water_quality_summary",
        "description": "获取当前鱼塘水质摘要和关键指标。",
        "inputSchema": {
            "type": "object",
            "properties": {"pondId": {"type": "string"}},
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "overview": {"type": "string"},
                "metrics": {"type": "array"},
                "riskLevel": {"type": "string"},
                "updatedAt": {"type": "string"},
                "sourceMode": {"type": "string"},
            },
        },
        "handler": get_water_quality_summary,
    },
    "get_feeding_recommendation": {
        "name": "get_feeding_recommendation",
        "description": "基于实时水质和投喂规则生成当前投喂建议。",
        "inputSchema": {
            "type": "object",
            "properties": {"pondId": {"type": "string"}},
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "recommendation": {"type": "string"},
                "confidence": {"type": "number"},
                "factors": {"type": "object"},
                "rationale": {"type": "array"},
                "sourceMode": {"type": "string"},
            },
        },
        "handler": get_feeding_recommendation,
    },
    "get_alert_digest": {
        "name": "get_alert_digest",
        "description": "获取当前页面最近告警摘要。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pondId": {"type": "string"},
                "limit": {"type": "number"},
            },
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "total": {"type": "number"},
                "critical": {"type": "number"},
                "warning": {"type": "number"},
                "latest": {"type": "array"},
            },
        },
        "handler": get_alert_digest,
    },
    "get_device_status": {
        "name": "get_device_status",
        "description": "获取当前鱼塘设备在线状态摘要。",
        "inputSchema": {
            "type": "object",
            "properties": {"pondId": {"type": "string"}},
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "onlineCount": {"type": "number"},
                "offlineCount": {"type": "number"},
                "feederStatus": {"type": "string"},
                "cameraStatus": {"type": "string"},
            },
        },
        "handler": get_device_status,
    },
    "preview_manual_feeding_action": {
        "name": "preview_manual_feeding_action",
        "description": "生成一次手动投喂的预览确认信息，不执行真实动作。",
        "inputSchema": {
            "type": "object",
            "required": ["amount"],
            "properties": {
                "pondId": {"type": "string"},
                "amount": {"type": "number"},
            },
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "previewText": {"type": "string"},
                "riskLevel": {"type": "string"},
                "confirmToken": {"type": "string"},
                "mode": {"type": "string"},
            },
        },
        "handler": None,
    },
}


PAGE_TOOL_WHITELIST: Dict[str, List[str]] = {
    "global-chat": [
        "get_water_quality_summary",
        "get_feeding_recommendation",
        "get_alert_digest",
        "get_device_status",
    ],
    "fishery-dashboard": [
        "get_water_quality_summary",
        "get_alert_digest",
        "get_device_status",
    ],
    "feeding": [
        "get_water_quality_summary",
        "get_feeding_recommendation",
        "get_alert_digest",
        "get_device_status",
        "preview_manual_feeding_action",
    ],
    "water-quality": [
        "get_water_quality_summary",
        "get_alert_digest",
        "get_device_status",
    ],
    "growth": [
        "get_alert_digest",
        "get_device_status",
    ],
}


def get_allowed_tools(page_id: str) -> List[str]:
    return PAGE_TOOL_WHITELIST.get(page_id, PAGE_TOOL_WHITELIST["global-chat"])


def get_tool_schemas(page_id: str) -> List[Dict[str, Any]]:
    return [
        {
            "name": TOOL_DEFINITIONS[name]["name"],
            "description": TOOL_DEFINITIONS[name]["description"],
            "inputSchema": TOOL_DEFINITIONS[name]["inputSchema"],
            "outputSchema": TOOL_DEFINITIONS[name]["outputSchema"],
        }
        for name in get_allowed_tools(page_id)
    ]


def run_tool(name: str, **kwargs: Any) -> Dict[str, Any]:
    definition = TOOL_DEFINITIONS[name]
    handler = definition["handler"]
    if handler is None:
        raise ValueError(
            f"Tool {name} requires preview route and cannot be executed directly."
        )
    if "pondId" in kwargs and "pond_id" not in kwargs:
        kwargs["pond_id"] = kwargs.pop("pondId")
    if "currentIndex" in kwargs and "current_index" not in kwargs:
        kwargs["current_index"] = kwargs.pop("currentIndex")
    return handler(**kwargs)
