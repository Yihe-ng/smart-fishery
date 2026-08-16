from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.sql import func

from app.db.base import Base


class GrowthRecord(Base):
    """生长识别记录：每次成功识别的可测摘要与月度评价结论。

    只保存跨页展示需要的摘要级字段；演示数据不落库，
    图片 Base64、掩码与单鱼检测明细不入库。
    """

    __tablename__ = "growth_records"

    id = Column(Integer, primary_key=True, index=True)
    pond_id = Column(String(32), nullable=False, index=True)  # 池塘编号
    source_type = Column(String(16), nullable=False)  # image / video
    recognized_at = Column(DateTime, nullable=False, index=True)  # 识别时间
    detected_count = Column(Integer, nullable=False, default=0)  # 检测总数
    measurable_count = Column(Integer, nullable=False, default=0)  # 可测尾数（样本数）
    unmeasurable_count = Column(Integer, nullable=False, default=0)  # 不可测尾数
    small_count = Column(Integer, nullable=False, default=0)
    normal_count = Column(Integer, nullable=False, default=0)
    large_count = Column(Integer, nullable=False, default=0)
    unassessed_count = Column(Integer, nullable=False, default=0)
    planned_frame_count = Column(Integer, nullable=True)
    completed_frame_count = Column(Integer, nullable=True)
    evaluable_frame_count = Column(Integer, nullable=True)
    detection_occurrence_count = Column(Integer, nullable=True)
    measurable_occurrence_count = Column(Integer, nullable=True)
    culture_month = Column(Integer, nullable=True)  # 养殖月数（3-15，未选择为 NULL）
    stocking_avg_length_cm = Column(Float, nullable=True)  # 投苗平均全长 cm
    avg_body_length_cm = Column(Float, nullable=False, default=0)  # 可测鱼平均全长 cm
    avg_weight_g = Column(Float, nullable=False, default=0)  # 可测鱼平均体重 g
    reference_length_cm = Column(Float, nullable=True)
    small_threshold_cm = Column(Float, nullable=True)
    large_threshold_cm = Column(Float, nullable=True)
    trimmed_mean_length_cm = Column(Float, nullable=True)
    all_measurable_avg_length_cm = Column(Float, nullable=True)
    cohort_status = Column(String(24), nullable=True)  # 群体状态 small/normal/large/insufficient/unassessed
    advice = Column(Text, nullable=True)  # 管理建议
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
