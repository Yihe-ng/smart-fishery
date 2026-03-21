from typing import Any, Callable, Dict, List

from app.agent.mock_data import (
    get_mock_alerts,
    get_mock_devices,
    get_mock_feeding_config,
    get_mock_water_quality,
)


def get_water_quality_summary(pond_id: str | None = None) -> Dict[str, Any]:
    water = get_mock_water_quality(pond_id)
    return {
        "overview": water["overview"],
        "metrics": water["metrics"],
        "riskLevel": water["riskLevel"],
        "updatedAt": water["updatedAt"],
        "sourceMode": water["sourceMode"],
    }


def get_feeding_recommendation(pond_id: str | None = None) -> Dict[str, Any]:
    water = get_mock_water_quality(pond_id)
    config = get_mock_feeding_config()
    return {
        "recommendation": "建议维持常规投喂频次，单次投喂量保守 500-600g，并先确认亚硝酸盐传感器状态。",
        "confidence": 0.73,
        "factors": {
            "feedCoefficient": config["feedCoefficient"],
            "frequency": config["frequency"],
            "temperature": 25.5,
            "dissolvedOxygen": 6.8,
        },
        "rationale": [
            "当前水温处于适宜区间。",
            "溶氧虽未触发停喂阈值，但处于保守区间。",
            "亚硝酸盐传感器离线，建议暂不激进加料。",
        ],
        "sourceMode": water["sourceMode"],
    }


def get_alert_digest(pond_id: str | None = None, limit: int = 3) -> Dict[str, Any]:
    _ = pond_id
    alerts = get_mock_alerts(limit)
    critical = sum(1 for alert in alerts if alert["level"] == "critical")
    warning = sum(1 for alert in alerts if alert["level"] == "warning")
    return {
        "total": len(alerts),
        "critical": critical,
        "warning": warning,
        "latest": [
            {
                "id": alert["id"],
                "title": alert["title"],
                "level": alert["level"],
                "status": alert["status"],
                "createTime": alert["create_time"],
            }
            for alert in alerts
        ],
    }


def get_device_status(pond_id: str | None = None) -> Dict[str, Any]:
    _ = pond_id
    devices = get_mock_devices()
    online = sum(1 for device in devices if device["status"] == "online")
    offline = len(devices) - online
    return {
        "onlineCount": online,
        "offlineCount": offline,
        "feederStatus": "online" if online >= 3 else "warning",
        "cameraStatus": "online",
    }


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
        "description": "基于 mock 水质和投喂配置生成当前投喂建议。",
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
    return handler(**kwargs)
