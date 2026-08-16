"""生长识别记录：识别成功后落库的可测摘要与月度评价结论。

写入由前端在识别/重评成功时触发（演示数据不上报）；
读取供前端「生长记录」历史页分页展示。
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.growth import GrowthRecord
from app.schemas.base import BaseResponse
from app.schemas.growth_record import (
    GrowthRecordAssessmentUpdate,
    GrowthRecordCreate,
    GrowthRecordHistoryResponse,
    GrowthRecordResponse,
)

router = APIRouter()


def _utc_naive(value: datetime) -> datetime:
    """SQLite 以无时区字段保存 UTC，统一输入口径后再入库/查询。"""
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _utc_aware(value: datetime | None) -> datetime | None:
    """响应层为 SQLite 的 UTC 无时区值补回时区，避免前端按本地时间误解析。"""
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def _to_response(record: GrowthRecord) -> GrowthRecordResponse:
    return GrowthRecordResponse(
        id=record.id,
        pondId=record.pond_id,
        sourceType=record.source_type,
        recognizedAt=_utc_aware(record.recognized_at),
        detectedCount=record.detected_count,
        measurableCount=record.measurable_count,
        unmeasurableCount=record.unmeasurable_count,
        small=record.small_count,
        normal=record.normal_count,
        large=record.large_count,
        unassessed=record.unassessed_count,
        plannedFrameCount=record.planned_frame_count,
        completedFrameCount=record.completed_frame_count,
        evaluableFrameCount=record.evaluable_frame_count,
        detectionOccurrenceCount=record.detection_occurrence_count,
        measurableOccurrenceCount=record.measurable_occurrence_count,
        cultureMonth=record.culture_month,
        stockingAvgLengthCm=record.stocking_avg_length_cm,
        avgBodyLengthCm=record.avg_body_length_cm,
        avgWeightG=record.avg_weight_g,
        referenceLengthCm=record.reference_length_cm,
        smallThresholdCm=record.small_threshold_cm,
        largeThresholdCm=record.large_threshold_cm,
        trimmedMeanLengthCm=record.trimmed_mean_length_cm,
        allMeasurableAvgLengthCm=record.all_measurable_avg_length_cm,
        cohortStatus=record.cohort_status,
        advice=record.advice,
        createdAt=_utc_aware(record.created_at),
        updatedAt=_utc_aware(record.updated_at),
    )


@router.post("/records", response_model=BaseResponse[GrowthRecordResponse])
def create_growth_record(record: GrowthRecordCreate, db: Session = Depends(get_db)):
    db_record = GrowthRecord(
        pond_id=record.pondId,
        source_type=record.sourceType,
        recognized_at=_utc_naive(record.recognizedAt),
        detected_count=record.detectedCount,
        measurable_count=record.measurableCount,
        unmeasurable_count=record.unmeasurableCount,
        small_count=record.small,
        normal_count=record.normal,
        large_count=record.large,
        unassessed_count=record.unassessed,
        planned_frame_count=record.plannedFrameCount,
        completed_frame_count=record.completedFrameCount,
        evaluable_frame_count=record.evaluableFrameCount,
        detection_occurrence_count=record.detectionOccurrenceCount,
        measurable_occurrence_count=record.measurableOccurrenceCount,
        culture_month=record.cultureMonth,
        stocking_avg_length_cm=record.stockingAvgLengthCm,
        avg_body_length_cm=record.avgBodyLengthCm,
        avg_weight_g=record.avgWeightG,
        reference_length_cm=record.referenceLengthCm,
        small_threshold_cm=record.smallThresholdCm,
        large_threshold_cm=record.largeThresholdCm,
        trimmed_mean_length_cm=record.trimmedMeanLengthCm,
        all_measurable_avg_length_cm=record.allMeasurableAvgLengthCm,
        cohort_status=record.cohortStatus,
        advice=record.advice,
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return BaseResponse[GrowthRecordResponse](code=200, msg="保存成功", data=_to_response(db_record))


@router.get("/records", response_model=BaseResponse[GrowthRecordHistoryResponse])
def get_growth_records(
    pond_id: Optional[str] = Query(None),
    source_type: Optional[str] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(GrowthRecord)
    if pond_id:
        query = query.filter(GrowthRecord.pond_id == pond_id)
    if source_type:
        query = query.filter(GrowthRecord.source_type == source_type)
    if start_time:
        query = query.filter(GrowthRecord.recognized_at >= _utc_naive(start_time))
    if end_time:
        query = query.filter(GrowthRecord.recognized_at <= _utc_naive(end_time))
    total = query.count()
    records = (
        query.order_by(desc(GrowthRecord.recognized_at), desc(GrowthRecord.id))
        .offset((page_num - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return BaseResponse[GrowthRecordHistoryResponse](
        code=200,
        msg="获取成功",
        data=GrowthRecordHistoryResponse(
            data=[_to_response(item) for item in records], total=total
        ),
    )


@router.get("/records/latest", response_model=BaseResponse[Optional[GrowthRecordResponse]])
def get_latest_growth_record(
    pond_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """某池塘最近一次识别记录，供前端在本地缓存为空时从数据库恢复摘要。"""
    query = db.query(GrowthRecord)
    if pond_id:
        query = query.filter(GrowthRecord.pond_id == pond_id)
    record = query.order_by(desc(GrowthRecord.recognized_at), desc(GrowthRecord.id)).first()
    if not record:
        return BaseResponse[Optional[GrowthRecordResponse]](code=200, msg="暂无识别记录", data=None)
    return BaseResponse[Optional[GrowthRecordResponse]](code=200, msg="获取成功", data=_to_response(record))


@router.put("/records/{record_id}", response_model=BaseResponse[GrowthRecordResponse])
def update_growth_record_assessment(
    record_id: int,
    update: GrowthRecordAssessmentUpdate,
    db: Session = Depends(get_db),
):
    """轻量重评后仅更新月度评价相关字段，不产生新的历史行。"""
    record = db.query(GrowthRecord).filter(GrowthRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="识别记录不存在")

    if "cultureMonth" in update.model_fields_set:
        record.culture_month = update.cultureMonth
    if "stockingAvgLengthCm" in update.model_fields_set:
        record.stocking_avg_length_cm = update.stockingAvgLengthCm
    if "referenceLengthCm" in update.model_fields_set:
        record.reference_length_cm = update.referenceLengthCm
    if "smallThresholdCm" in update.model_fields_set:
        record.small_threshold_cm = update.smallThresholdCm
    if "largeThresholdCm" in update.model_fields_set:
        record.large_threshold_cm = update.largeThresholdCm
    if "trimmedMeanLengthCm" in update.model_fields_set:
        record.trimmed_mean_length_cm = update.trimmedMeanLengthCm
    if "allMeasurableAvgLengthCm" in update.model_fields_set:
        record.all_measurable_avg_length_cm = update.allMeasurableAvgLengthCm
    if "cohortStatus" in update.model_fields_set:
        record.cohort_status = update.cohortStatus
    if "advice" in update.model_fields_set:
        record.advice = update.advice

    db.commit()
    db.refresh(record)
    return BaseResponse[GrowthRecordResponse](code=200, msg="更新成功", data=_to_response(record))


@router.delete("/records/{record_id}", response_model=BaseResponse[None])
def delete_growth_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(GrowthRecord).filter(GrowthRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="识别记录不存在")

    db.delete(record)
    db.commit()
    return BaseResponse[None](code=200, msg="删除成功", data=None)
