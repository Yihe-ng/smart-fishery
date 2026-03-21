from datetime import datetime
from typing import Any, Dict, List

from app.agent.config import get_ai_settings
from app.api.v1.endpoints.alert import mock_alerts
from app.api.v1.endpoints.device import mock_devices
from app.api.v1.endpoints.feeding import mock_feeding_config, mock_feeding_logs


def get_mock_pond(pond_id: str | None) -> Dict[str, Any]:
    target_id = pond_id or "pond-001"
    mode = get_ai_settings().ai_mode
    return {
        "pondId": target_id,
        "name": f"智慧鱼塘 {target_id}",
        "sourceMode": mode,
    }


def get_mock_water_quality(pond_id: str | None) -> Dict[str, Any]:
    _ = pond_id
    mode = get_ai_settings().ai_mode
    return {
        "overview": "当前水质整体稳定，溶氧略偏保守，亚硝酸盐传感器离线。",
        "riskLevel": "warning",
        "updatedAt": datetime.now().isoformat(),
        "sourceMode": mode,
        "metrics": [
            {
                "key": "temperature",
                "label": "水温",
                "value": 25.5,
                "unit": "℃",
                "status": "normal",
            },
            {"key": "ph", "label": "pH", "value": 7.2, "unit": "", "status": "normal"},
            {
                "key": "dissolved_oxygen",
                "label": "溶氧",
                "value": 6.8,
                "unit": "mg/L",
                "status": "warning",
            },
            {
                "key": "ammonia_nitrogen",
                "label": "氨氮",
                "value": 0.3,
                "unit": "mg/L",
                "status": "normal",
            },
            {
                "key": "nitrite",
                "label": "亚硝酸盐",
                "value": 0.05,
                "unit": "mg/L",
                "status": "warning",
            },
        ],
    }


def get_mock_alerts(limit: int = 5) -> List[Dict[str, Any]]:
    return mock_alerts[:limit]


def get_mock_devices() -> List[Dict[str, Any]]:
    return mock_devices


def get_mock_feeding_config() -> Dict[str, Any]:
    return {
        "feedCoefficient": mock_feeding_config["feed_coefficient"],
        "frequency": mock_feeding_config["frequency"],
        "feedSize": mock_feeding_config["feed_size"],
    }


def get_mock_feeding_logs(limit: int = 5) -> List[Dict[str, Any]]:
    return [
        {
            "id": log["id"],
            "feedTime": log["feed_time"],
            "amount": log["amount"],
            "status": log["status"],
            "triggerType": log["trigger_type"],
        }
        for log in mock_feeding_logs[:limit]
    ]
