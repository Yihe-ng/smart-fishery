from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.water import AlertRecord, SensorDevice, WaterQualityData
from app.services.water_quality_dashboard import (
    build_alerts_payload,
    build_devices_payload,
    build_metrics_payload,
    evaluate_metric_status,
    format_collect_time,
)


STATUS_MAP = {
    "正常": "normal",
    "警戒": "warning",
    "危险": "critical",
}


@contextmanager
def agent_db_session(db: Session | None = None) -> Iterator[Session]:
    if db is not None:
        yield db
        return

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _get_dashboard_records(session: Session) -> list[WaterQualityData]:
    return (
        session.query(WaterQualityData)
        .order_by(WaterQualityData.collect_time.asc())
        .all()
    )


def get_frame_records(
    current_index: int | None = None,
    db: Session | None = None,
) -> tuple[WaterQualityData | None, WaterQualityData | None]:
    if current_index is None:
        return None, None

    with agent_db_session(db) as session:
        records = _get_dashboard_records(session)
        if not records:
            return None, None
        bounded_index = current_index if 0 <= current_index < len(records) else 0
        current_record = records[bounded_index]
        previous_record = records[bounded_index - 1] if bounded_index > 0 else None
        return current_record, previous_record


def get_pond_summary(
    pond_id: str | None,
    current_index: int | None = None,
    db: Session | None = None,
) -> dict[str, Any]:
    current_record, _ = get_frame_records(current_index, db=db)
    target_id = current_record.pond_id if current_record is not None else (pond_id or "pond-001")
    return {
        "pondId": target_id,
        "name": f"智慧鱼塘 {target_id}",
        "sourceMode": "real",
    }


def get_latest_water_record(
    pond_id: str | None = None, db: Session | None = None
) -> WaterQualityData | None:
    with agent_db_session(db) as session:
        query = session.query(WaterQualityData)
        if pond_id:
            query = query.filter(WaterQualityData.pond_id == pond_id)
        return query.order_by(desc(WaterQualityData.collect_time)).first()


def get_previous_water_record(
    current_record: WaterQualityData | None,
    pond_id: str | None = None,
    db: Session | None = None,
) -> WaterQualityData | None:
    if current_record is None:
        return None

    with agent_db_session(db) as session:
        query = session.query(WaterQualityData)
        if pond_id:
            query = query.filter(WaterQualityData.pond_id == pond_id)
        return (
            query.filter(WaterQualityData.collect_time < current_record.collect_time)
            .order_by(desc(WaterQualityData.collect_time))
            .first()
        )


def resolve_water_records(
    pond_id: str | None = None,
    current_index: int | None = None,
    db: Session | None = None,
) -> tuple[WaterQualityData | None, WaterQualityData | None]:
    current_record, previous_record = get_frame_records(current_index, db=db)
    if current_record is not None:
        return current_record, previous_record
    current_record = get_latest_water_record(pond_id, db=db)
    previous_record = get_previous_water_record(current_record, pond_id, db=db)
    return current_record, previous_record


def _build_water_metrics(
    current_record: WaterQualityData, previous_record: WaterQualityData | None
) -> list[dict[str, Any]]:
    payload = build_metrics_payload(current_record, previous_record)
    return [
        {
            "key": metric["key"],
            "label": metric["label"],
            "value": metric["value"],
            "unit": metric["unit"],
            "status": STATUS_MAP.get(metric["statusText"], "normal"),
        }
        for metric in payload.values()
    ]


def _build_water_overview(metrics: list[dict[str, Any]]) -> str:
    if not metrics:
        return "当前暂无水质数据，无法生成实时摘要。"

    critical = [item for item in metrics if item["status"] == "critical"]
    warning = [item for item in metrics if item["status"] == "warning"]
    temperature = next((item for item in metrics if item["key"] == "temperature"), None)
    dissolved_oxygen = next(
        (item for item in metrics if item["key"] == "dissolvedOxygen"),
        None,
    )
    summary_parts: list[str] = []
    if temperature:
        summary_parts.append(f"水温 {temperature['value']}{temperature['unit']}")
    if dissolved_oxygen:
        summary_parts.append(f"溶氧 {dissolved_oxygen['value']}{dissolved_oxygen['unit']}")

    if critical:
        risk_text = "存在严重水质风险"
    elif warning:
        risk_text = "存在需要关注的水质波动"
    else:
        risk_text = "整体处于稳定范围"
    return f"当前{'，'.join(summary_parts)}，{risk_text}。"


def get_water_quality_summary_data(
    pond_id: str | None = None,
    current_index: int | None = None,
    db: Session | None = None,
) -> dict[str, Any]:
    current_record, previous_record = resolve_water_records(
        pond_id=pond_id,
        current_index=current_index,
        db=db,
    )
    if current_record is None:
        return {
            "overview": "当前暂无水质数据，无法生成实时摘要。",
            "metrics": [],
            "riskLevel": "unknown",
            "updatedAt": "",
            "sourceMode": "real",
        }

    metrics = _build_water_metrics(current_record, previous_record)
    risk_level = "low"
    if any(item["status"] == "critical" for item in metrics):
        risk_level = "critical"
    elif any(item["status"] == "warning" for item in metrics):
        risk_level = "warning"

    return {
        "overview": _build_water_overview(metrics),
        "metrics": metrics,
        "riskLevel": risk_level,
        "updatedAt": format_collect_time(current_record.collect_time),
        "sourceMode": "real",
    }


def get_alert_digest_data(
    pond_id: str | None = None,
    limit: int = 3,
    current_index: int | None = None,
    db: Session | None = None,
) -> dict[str, Any]:
    current_record, _ = get_frame_records(current_index, db=db)
    if current_record is not None:
        alerts = build_alerts_payload(current_record)[:limit]
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
                    "createTime": alert["createTime"],
                }
                for alert in alerts
            ],
        }

    with agent_db_session(db) as session:
        query = session.query(AlertRecord)
        if pond_id:
            query = query.filter(AlertRecord.pond_id == pond_id)
        total = query.count()
        records = query.order_by(desc(AlertRecord.collect_time)).limit(limit).all()
        critical = query.filter(AlertRecord.alert_level == "critical").count() if total else 0
        warning = query.filter(AlertRecord.alert_level == "warning").count() if total else 0

    return {
        "total": total,
        "critical": critical,
        "warning": warning,
        "latest": [
            {
                "id": str(record.id),
                "title": record.alert_type,
                "level": record.alert_level,
                "status": "resolved" if record.is_resolved else "pending",
                "createTime": format_collect_time(record.collect_time),
            }
            for record in records
        ],
    }


def _build_device_summary_from_sensor_table(
    pond_id: str | None = None, db: Session | None = None
) -> dict[str, Any] | None:
    with agent_db_session(db) as session:
        query = session.query(SensorDevice)
        if pond_id:
            query = query.filter(SensorDevice.pond_id == pond_id)
        devices = query.all()

    if not devices:
        return None

    online_statuses = {"active", "online"}
    online = [device for device in devices if device.status in online_statuses]
    offline = [device for device in devices if device.status not in online_statuses]
    feeder_online = any("feeder" in device.device_id.lower() for device in online)
    camera_online = any("camera" in device.device_id.lower() for device in online)
    return {
        "onlineCount": len(online),
        "offlineCount": len(offline),
        "feederStatus": "online" if feeder_online or len(online) >= 1 else "warning",
        "cameraStatus": "online" if camera_online or len(online) >= 1 else "offline",
    }


def get_device_status_data(
    pond_id: str | None = None,
    current_index: int | None = None,
    db: Session | None = None,
) -> dict[str, Any]:
    current_record, _ = get_frame_records(current_index, db=db)
    if current_record is not None:
        devices = build_devices_payload(current_record)
        online = sum(1 for device in devices if device["status"] == "online")
        offline = len(devices) - online
        return {
            "onlineCount": online,
            "offlineCount": offline,
            "feederStatus": "online" if online >= 3 else "warning",
            "cameraStatus": "online" if online >= 1 else "offline",
        }

    sensor_summary = _build_device_summary_from_sensor_table(pond_id, db=db)
    if sensor_summary is not None:
        return sensor_summary

    current_record = get_latest_water_record(pond_id, db=db)
    devices = build_devices_payload(current_record)
    online = sum(1 for device in devices if device["status"] == "online")
    offline = len(devices) - online
    return {
        "onlineCount": online,
        "offlineCount": offline,
        "feederStatus": "online" if online >= 3 else "warning",
        "cameraStatus": "online" if online >= 1 else "offline",
    }


def get_water_quality_snapshot(
    pond_id: str | None = None,
    current_index: int | None = None,
    db: Session | None = None,
) -> dict[str, float] | None:
    current_record, _ = resolve_water_records(
        pond_id=pond_id,
        current_index=current_index,
        db=db,
    )
    if current_record is None:
        return None
    return {
        "dissolved_oxygen": current_record.dissolved_oxygen,
        "temperature": current_record.temperature,
        "ph": current_record.ph_value,
        "ammonia_nitrogen": current_record.ammonia_nitrogen,
        "nitrite": current_record.nitrite,
    }


def get_water_quality_metric_status(
    pond_id: str | None = None,
    current_index: int | None = None,
    db: Session | None = None,
) -> dict[str, str] | None:
    snapshot = get_water_quality_snapshot(
        pond_id=pond_id,
        current_index=current_index,
        db=db,
    )
    if snapshot is None:
        return None

    return {
        "dissolved_oxygen": STATUS_MAP.get(
            evaluate_metric_status("dissolvedOxygen", snapshot["dissolved_oxygen"]),
            "normal",
        ),
        "temperature": STATUS_MAP.get(
            evaluate_metric_status("temperature", snapshot["temperature"]),
            "normal",
        ),
        "ph": STATUS_MAP.get(
            evaluate_metric_status("ph", snapshot["ph"]),
            "normal",
        ),
        "ammonia_nitrogen": STATUS_MAP.get(
            evaluate_metric_status("ammoniaNitrogen", snapshot["ammonia_nitrogen"]),
            "normal",
        ),
        "nitrite": STATUS_MAP.get(
            evaluate_metric_status("nitrite", snapshot["nitrite"]),
            "normal",
        ),
    }
