from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.water import WaterQualityData

MetricStatusText = str


@dataclass(frozen=True)
class RangeRule:
    min: float | None = None
    max: float | None = None


@dataclass(frozen=True)
class MetricRule:
    label: str
    unit: str
    ideal: RangeRule
    warning: RangeRule
    critical: RangeRule


METRIC_RULES: dict[str, MetricRule] = {
    "temperature": MetricRule(
        label="水温",
        unit="℃",
        ideal=RangeRule(min=23.0, max=28.0),
        warning=RangeRule(min=20.0, max=30.0),
        critical=RangeRule(min=18.0, max=33.0),
    ),
    "ph": MetricRule(
        label="pH值",
        unit="",
        ideal=RangeRule(min=8.7, max=9.0),
        warning=RangeRule(min=8.0, max=9.0),
        critical=RangeRule(min=7.5, max=9.2),
    ),
    "dissolvedOxygen": MetricRule(
        label="溶氧",
        unit="mg/L",
        ideal=RangeRule(min=5.3),
        warning=RangeRule(min=4.0),
        critical=RangeRule(min=3.0),
    ),
    "ammoniaNitrogen": MetricRule(
        label="氨氮",
        unit="mg/L",
        ideal=RangeRule(max=0.06),
        warning=RangeRule(max=0.15),
        critical=RangeRule(max=0.30),
    ),
    "nitrite": MetricRule(
        label="亚硝酸盐",
        unit="mg/L",
        ideal=RangeRule(max=0.06),
        warning=RangeRule(max=0.10),
        critical=RangeRule(max=0.20),
    ),
}

DB_FIELD_MAP = {
    "temperature": "temperature",
    "ph": "ph_value",
    "dissolvedOxygen": "dissolved_oxygen",
    "ammoniaNitrogen": "ammonia_nitrogen",
    "nitrite": "nitrite",
}

KEY_ALIASES = {
    "ph_value": "ph",
    "dissolved_oxygen": "dissolvedOxygen",
    "ammonia_nitrogen": "ammoniaNitrogen",
}

DEVICE_META = {
    "temperature": {"id": "temp-001", "name": "水温传感器", "type": "temperature", "location": "1号池东侧"},
    "ph": {"id": "ph-001", "name": "pH传感器", "type": "ph", "location": "1号池中心"},
    "dissolvedOxygen": {
        "id": "do-001",
        "name": "溶氧传感器",
        "type": "dissolved_oxygen",
        "location": "1号池西侧",
    },
    "ammoniaNitrogen": {
        "id": "nh3-001",
        "name": "氨氮传感器",
        "type": "ammonia_nitrogen",
        "location": "总进水口",
    },
    "nitrite": {
        "id": "no2-001",
        "name": "亚硝酸盐传感器",
        "type": "nitrite",
        "location": "总出水口",
    },
}


def range_to_dict(rule: RangeRule) -> dict[str, float]:
    payload: dict[str, float] = {}
    if rule.min is not None:
        payload["min"] = rule.min
    if rule.max is not None:
        payload["max"] = rule.max
    return payload


def get_threshold_config() -> dict[str, dict[str, Any]]:
    return {
        key: {
            "label": rule.label,
            "unit": rule.unit,
            "ideal": range_to_dict(rule.ideal),
            "warning": range_to_dict(rule.warning),
            "critical": range_to_dict(rule.critical),
        }
        for key, rule in METRIC_RULES.items()
    }


def _is_below(rule: RangeRule, value: float) -> bool:
    return rule.min is not None and value < rule.min


def _is_above(rule: RangeRule, value: float) -> bool:
    return rule.max is not None and value > rule.max


def evaluate_metric_status(metric_key: str, value: float) -> MetricStatusText:
    metric_key = KEY_ALIASES.get(metric_key, metric_key)
    rule = METRIC_RULES[metric_key]
    if _is_below(rule.critical, value) or _is_above(rule.critical, value):
        return "危险"
    if _is_below(rule.warning, value) or _is_above(rule.warning, value):
        return "警戒"
    return "正常"


def is_metric_ideal(metric_key: str, value: float) -> bool:
    rule = METRIC_RULES[metric_key].ideal
    if rule.min is not None and value < rule.min:
        return False
    if rule.max is not None and value > rule.max:
        return False
    return True


def format_collect_time(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M:%S")


def format_metric_number(value: float) -> str:
    if abs(value - round(value)) < 0.01:
        return str(int(round(value)))
    precision = 1 if abs(value) >= 10 else 2
    return f"{value:.{precision}f}".rstrip("0").rstrip(".")


def format_trend_text(previous_value: float | None, current_value: float) -> str:
    if previous_value is None:
        return "趋势 --"

    delta = current_value - previous_value
    if abs(delta) < 0.01:
        return "趋势 持平"
    sign = "+" if delta > 0 else ""
    return f"趋势 {sign}{format_metric_number(delta)}"


def record_to_water_quality_payload(record: WaterQualityData | None) -> dict[str, Any] | None:
    if record is None:
        return None

    return {
        "id": str(record.id),
        "pondId": record.pond_id,
        "temperature": record.temperature,
        "ph": record.ph_value,
        "dissolvedOxygen": record.dissolved_oxygen,
        "ammoniaNitrogen": record.ammonia_nitrogen,
        "nitrite": record.nitrite,
        "collectTime": format_collect_time(record.collect_time),
        "status": record.status,
    }


def build_metrics_payload(
    current_record: WaterQualityData, previous_record: WaterQualityData | None
) -> dict[str, dict[str, Any]]:
    metrics: dict[str, dict[str, Any]] = {}
    for metric_key, rule in METRIC_RULES.items():
        current_value = getattr(current_record, DB_FIELD_MAP[metric_key])
        previous_value = None
        if previous_record is not None:
            previous_value = getattr(previous_record, DB_FIELD_MAP[metric_key])
        metrics[metric_key] = {
            "key": metric_key,
            "label": rule.label,
            "value": current_value,
            "unit": rule.unit,
            "statusText": evaluate_metric_status(metric_key, current_value),
            "trendText": format_trend_text(previous_value, current_value),
            "isIdeal": is_metric_ideal(metric_key, current_value),
        }
    return metrics


def build_devices_payload(current_record: WaterQualityData | None) -> list[dict[str, Any]]:
    if current_record is None:
        return [
            {
                **meta,
                "status": "offline",
                "lastOnlineTime": None,
                "lastData": None,
                "unit": METRIC_RULES[metric_key].unit,
            }
            for metric_key, meta in DEVICE_META.items()
        ]

    devices = []
    for metric_key, meta in DEVICE_META.items():
        value = getattr(current_record, DB_FIELD_MAP[metric_key])
        devices.append(
            {
                **meta,
                "status": "online",
                "lastOnlineTime": format_collect_time(current_record.collect_time),
                "lastData": value,
                "unit": METRIC_RULES[metric_key].unit,
            }
        )
    return devices


def build_alerts_payload(current_record: WaterQualityData | None) -> list[dict[str, Any]]:
    if current_record is None:
        return []

    alerts: list[dict[str, Any]] = []
    collect_time = format_collect_time(current_record.collect_time)
    for metric_key, rule in METRIC_RULES.items():
        value = getattr(current_record, DB_FIELD_MAP[metric_key])
        status_text = evaluate_metric_status(metric_key, value)
        if status_text == "正常":
            continue

        level = "critical" if status_text == "危险" else "warning"
        title_suffix = "过低" if _is_below(rule.warning, value) or _is_below(rule.critical, value) else "过高"
        threshold_rule = rule.critical if level == "critical" else rule.warning
        threshold_value = threshold_rule.min if "低" in title_suffix else threshold_rule.max
        threshold_label = "下限" if "低" in title_suffix else "上限"
        unit_suffix = rule.unit
        current_value_text = format_metric_number(value)
        threshold_value_text = format_metric_number(threshold_value or 0)
        alerts.append(
            {
                "id": f"frame-{current_record.id}-{metric_key}-{level}",
                "type": "water_quality",
                "level": level,
                "title": f"{rule.label}{title_suffix}",
                "message": (
                    f"当前{rule.label} {current_value_text}{unit_suffix}，"
                    f"达到{status_text}阈值{threshold_label} {threshold_value_text}{unit_suffix}"
                ),
                "createTime": collect_time,
                "status": "pending",
                "relatedDevice": DEVICE_META[metric_key]["id"],
            }
        )
    return alerts


def get_dashboard_frame(db: Session, index: int) -> dict[str, Any]:
    records = db.query(WaterQualityData).order_by(WaterQualityData.collect_time.asc()).all()
    total = len(records)
    if total == 0:
        return {
            "index": 0,
            "nextIndex": 0,
            "total": 0,
            "hasNext": False,
            "pondId": None,
            "collectTime": None,
            "waterQuality": None,
            "previousWaterQuality": None,
            "metrics": {},
            "devices": build_devices_payload(None),
            "alerts": [],
        }

    current_index = index if 0 <= index < total else 0
    previous_record = records[current_index - 1] if current_index > 0 else None
    current_record = records[current_index]
    return {
        "index": current_index,
        "nextIndex": (current_index + 1) % total,
        "total": total,
        "hasNext": total > 1,
        "pondId": current_record.pond_id,
        "collectTime": format_collect_time(current_record.collect_time),
        "waterQuality": record_to_water_quality_payload(current_record),
        "previousWaterQuality": record_to_water_quality_payload(previous_record),
        "metrics": build_metrics_payload(current_record, previous_record),
        "devices": build_devices_payload(current_record),
        "alerts": build_alerts_payload(current_record),
    }
