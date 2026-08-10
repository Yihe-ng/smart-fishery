"""准入策略模块：把 A5 阶段“是否可测”的判定提取为可配置、可测试的独立策略。

设计目标：
1. 保留现有 strict 行为：可测 = 分类器通过 ∧ 分割置信足够 ∧ 几何测长成功；
2. 提供 geometry_rescue 影子策略：仅当分类器拒绝时，若几何测长成功、
   Mask 正常、鱼体不触边、无黏连/严重孔洞/主体缺失、无硬阻断原因码且长度
   无明显异常，才产生“候选救援”结果（只计算，不改变正式展示）；
3. 影子策略不设置分类概率下限（不因 p_measurable 低而拒绝救援）；
4. 不放松 touch_border；path_ambiguous / no_trusted_measurement_path 暂不救援；
5. 中心线不美观但最终数值合理时不自动阻断（路径质量问题不拦截准入）；
6. 保留原始几何置信度：分类器拒绝不把几何置信度清零（影子结果独立携带）。

正式管线默认 mode=strict、geometry_rescue_enabled=false，API 输出保持不变。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# 支持的模式
MODE_STRICT = "strict"
MODE_GEOMETRY_RESCUE = "geometry_rescue"
SUPPORTED_MODES = {MODE_STRICT, MODE_GEOMETRY_RESCUE}

# 硬阻断原因码：救援策略必须保持拒绝（不放松）
HARD_BLOCKING_CODES = frozenset(
    {"touch_border", "path_ambiguous", "no_trusted_measurement_path"}
)

# Mask 异常原因码：救援策略不得放行（黏连/严重孔洞/主体缺失）
MASK_ABNORMAL_CODES = frozenset(
    {"adhesion_secondary_component", "large_or_core_cutting_hole", "multiple_body_cores"}
)


@dataclass(frozen=True)
class AdmissionPolicyConfig:
    """准入策略配置（由 manifest 的 admission_policy 段提供）。"""

    mode: str = MODE_STRICT
    geometry_rescue_enabled: bool = False
    # 救援概率下限：None 表示不设下限（影子实验档位）；设置后分类概率低于
    # 该值的候选救援被阻断（审核数据：P<0.1 正确率仅 28%，P>=0.4 达 94%）
    min_rescue_probability: Optional[float] = None


@dataclass
class AdmissionEvaluation:
    """一次准入评估的完整结果。

    - strict 模式：与现有管线行为逐字段一致；
    - geometry_rescue 影子：`is_measurable` 为候选结论，`reason_codes` 追加
      `geometry_rescue` 标记，`geometry_confidence` 保留原始值（不被分类器拒绝清零）。
    """

    is_measurable: bool
    reason_codes: List[str]
    geometry_confidence: float
    rescued: bool = False
    rescue_blocked_by: List[str] = field(default_factory=list)
    # 影子策略的信号快照（供审计页面展示触发条件）
    signals: Dict[str, Any] = field(default_factory=dict)


def _collect_rescue_signals(
    *,
    classifier_is_measurable: bool,
    segmentation_is_sufficient: bool,
    geometry_is_measurable: bool,
    primary_length_px: Optional[float],
    touch_border: bool,
    adhesion_suspected: bool,
    path_ambiguous: bool,
    no_trusted_measurement_path: bool,
    mask_abnormal: bool,
    length_anomaly: bool,
    reason_codes: List[str],
    raw_geometry_confidence: Optional[float] = None,
    p_measurable: Optional[float] = None,
) -> Dict[str, Any]:
    """汇总救援策略所需的信号快照（只读，供页面与调试使用）。"""
    return {
        "classifier_is_measurable": classifier_is_measurable,
        "segmentation_is_sufficient": segmentation_is_sufficient,
        "geometry_is_measurable": geometry_is_measurable,
        "primary_length_px": primary_length_px,
        "touch_border": touch_border,
        "adhesion_suspected": adhesion_suspected,
        "path_ambiguous": path_ambiguous,
        "no_trusted_measurement_path": no_trusted_measurement_path,
        "mask_abnormal": mask_abnormal,
        "length_anomaly": length_anomaly,
        "reason_codes": list(reason_codes),
        "raw_geometry_confidence": raw_geometry_confidence,
        "p_measurable": p_measurable,
    }


def evaluate_admission(
    *,
    classifier_is_measurable: bool,
    segmentation_is_sufficient: bool,
    geometry_is_measurable: bool,
    measurement_succeeded: bool = True,
    primary_length_px: Optional[float] = None,
    reason_codes: Optional[List[str]] = None,
    geometry_confidence: Optional[float] = None,
    touch_border: bool = False,
    adhesion_suspected: bool = False,
    path_ambiguous: bool = False,
    no_trusted_measurement_path: bool = False,
    mask_abnormal: bool = False,
    length_anomaly: bool = False,
    p_measurable: Optional[float] = None,
    config: Optional[AdmissionPolicyConfig] = None,
) -> AdmissionEvaluation:
    """评估一条鱼的最终准入结论。

    参数语义：
    - classifier_is_measurable：分类器（含时序）最终概率 >= 阈值；
    - segmentation_is_sufficient：分割置信 >= min_confidence_for_measurement；
    - geometry_is_measurable：几何测长模块自身判定可测（is_measurable）；
    - measurement_succeeded：测长流程未抛异常（measurement_method 非 none）；
    - primary_length_px：主路径长度（>0 表示有可换算数值）；
    - reason_codes：测长模块产出原因码（含 touch_border/path_ambiguous 等）；
    - geometry_confidence：原始几何置信度；
    - touch_border / adhesion_suspected / path_ambiguous /
      no_trusted_measurement_path：由调用方从原因码或测长结果提取；
    - mask_abnormal：Mask 异常（黏连/严重孔洞/主体缺失）布尔汇总；
    - length_anomaly：长度异常标记（如与历史均值的偏离告警）；
    - p_measurable：分类器可测概率（影子救援下限 min_rescue_probability 使用）。

    strict 模式逐字段复刻现有 pipeline 行为：
    - 可测 = 分类器 ∧ 分割 ∧ 几何；
    - 分类器/分割不通过时几何置信度清零，原因码按 model_unmeasurable /
      segmentation_confidence_below_threshold / geometry_unmeasurable 顺序前插。
    """
    cfg = config or AdmissionPolicyConfig()
    if cfg.mode not in SUPPORTED_MODES:
        raise ValueError(
            f"不支持的准入模式 {cfg.mode!r}，可选：{sorted(SUPPORTED_MODES)}"
        )

    codes = list(reason_codes or [])
    raw_confidence = float(geometry_confidence) if geometry_confidence is not None else 0.0
    confidence = raw_confidence

    # ---- strict 判定（正式行为，保持不变） ----
    is_measurable = bool(
        classifier_is_measurable and segmentation_is_sufficient and geometry_is_measurable
    )
    if not classifier_is_measurable:
        confidence = 0.0
        codes.insert(0, "model_unmeasurable")
    if not segmentation_is_sufficient:
        confidence = 0.0
        codes.insert(0, "segmentation_confidence_below_threshold")
    if not geometry_is_measurable:
        codes.insert(0, "geometry_unmeasurable")

    evaluation = AdmissionEvaluation(
        is_measurable=is_measurable,
        reason_codes=codes,
        geometry_confidence=confidence,
        signals=_collect_rescue_signals(
            classifier_is_measurable=classifier_is_measurable,
            segmentation_is_sufficient=segmentation_is_sufficient,
            geometry_is_measurable=geometry_is_measurable,
            primary_length_px=primary_length_px,
            touch_border=touch_border,
            adhesion_suspected=adhesion_suspected,
            path_ambiguous=path_ambiguous,
            no_trusted_measurement_path=no_trusted_measurement_path,
            mask_abnormal=mask_abnormal,
            length_anomaly=length_anomaly,
            reason_codes=reason_codes or [],
            raw_geometry_confidence=raw_confidence,
            p_measurable=p_measurable,
        ),
    )

    # ---- geometry_rescue 影子评估（只计算，不改变正式结果） ----
    if (
        cfg.mode == MODE_GEOMETRY_RESCUE
        and cfg.geometry_rescue_enabled
        and not is_measurable
        and not classifier_is_measurable
    ):
        evaluation = _apply_geometry_rescue(evaluation, cfg)

    return evaluation


def _apply_geometry_rescue(
    evaluation: AdmissionEvaluation, cfg: AdmissionPolicyConfig
) -> AdmissionEvaluation:
    """应用几何救援影子策略：满足全部条件才产生候选救援结果。

    触发前提（缺一不可）：
    1. 分类器拒绝（调用方已在 evaluate_admission 中保证）；
    2. 几何测长成功（geometry_is_measurable 且 measurement_succeeded 且长度 > 0）；
    3. 分割置信足够（不放松分割门槛）；
    4. Mask 正常（无黏连/严重孔洞/主体缺失）；
    5. 鱼体不触边（不放松 touch_border）；
    6. 无硬阻断原因码（path_ambiguous / no_trusted_measurement_path 暂不救援）；
    7. 长度无明显异常；
    8. 若配置 min_rescue_probability，则 P(可测) 必须不低于该下限
       （审核数据：P<0.1 救援正确率仅 28%，P>=0.4 达 94%）。
    中心线不美观（路径问题）不自动阻断。
    """
    s = evaluation.signals
    blocked: List[str] = []
    if not s["geometry_is_measurable"]:
        blocked.append("geometry_failed")
    if not s["segmentation_is_sufficient"]:
        blocked.append("segmentation_insufficient")
    if s["touch_border"]:
        blocked.append("touch_border")
    if s["mask_abnormal"] or s["adhesion_suspected"]:
        blocked.append("mask_abnormal")
    if s["path_ambiguous"]:
        blocked.append("path_ambiguous")
    if s["no_trusted_measurement_path"]:
        blocked.append("no_trusted_measurement_path")
    if s["length_anomaly"]:
        blocked.append("length_anomaly")
    if not (s["primary_length_px"] or 0) > 0:
        blocked.append("no_length_px")
    if (
        cfg.min_rescue_probability is not None
        and (s.get("p_measurable") or 0.0) < cfg.min_rescue_probability
    ):
        blocked.append("probability_below_floor")

    if blocked:
        evaluation.rescue_blocked_by = blocked
        return evaluation

    # 救援成功：候选准入通过；保留原始几何置信度，原因码追加标记
    evaluation.is_measurable = True
    evaluation.rescued = True
    evaluation.geometry_confidence = float(s.get("raw_geometry_confidence", 0.0) or 0.0)
    evaluation.reason_codes = [c for c in evaluation.reason_codes if c != "model_unmeasurable"]
    evaluation.reason_codes.insert(0, "geometry_rescue")
    return evaluation
