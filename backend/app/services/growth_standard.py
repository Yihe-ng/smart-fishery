"""石斑鱼月度生长评价服务（养殖标准的唯一解释者）。

职责边界：模型清单（`config/growth/pipeline.final.json`）负责"怎么测"——分割、
分类、几何测长与像素→厘米换算；本模块负责"测出来怎么评"——读取养殖标准
`config/growth/grouper_growth_standard.json`，把体长换成月度生长状态、群体状态
和确定性管理建议。两者的参数互不重叠，任何一侧都不得复制另一侧的口径。

模块不做推理、不读图片、不写数据库；除首次读取配置文件外没有副作用。
"""

from __future__ import annotations

import json
import math
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from app.core.config import settings

SUPPORTED_SCHEMA_VERSION = 1
# 养殖标准必须覆盖的月份区间（投苗后第 3–15 个月，见配置目录 README §2）
FIRST_MONTH = 3
LAST_MONTH = 15

STATUS_TEXTS = {
    "small": "偏小",
    "normal": "正常",
    "large": "偏大",
    "unassessed": "未评估",
    "unmeasurable": "不可测",
}

# 群体五档管理建议文案（方案 §8.2 原文）。由确定性规则生成，不经大模型，
# 只提出核查方向，不声称系统已获得投喂、摄食、密度或健康记录，也不给出投喂克数。
COHORT_ADVICE = {
    "small": (
        "当前群体生长低于本月参考下限。建议优先核查投喂执行和摄食情况，"
        "并结合饲料适配、养殖密度、规格分化及健康状态综合判断，再决定是否调整投喂。"
    ),
    "normal": "当前生长达到本月综合参考范围，建议维持现有投喂节奏，继续记录摄食情况并定期复测。",
    "large": (
        "当前群体生长高于本月正常参考范围。建议先确认养殖月份和投苗体长，"
        "无需因为体长偏大继续增加投喂，并持续核对投喂执行情况。"
    ),
    "insufficient": "有效样本不足，建议补充一张至少包含 3 条可测鱼的图片后再判断。",
    "unassessed": "已完成体长测量；选择养殖月份并填写投苗体长后，才能生成生长与投喂建议。",
}


class GrowthStandardError(ValueError):
    """养殖标准缺失、结构非法或数值越界。

    调用方（图片识别端点）捕获它后必须保留模型测量结果、把可测鱼置为
    "未评估"，禁止回退到任何未配置的固定阈值（方案 §9.4）。
    """


@dataclass(frozen=True)
class MonthlyRule:
    """某个养殖月份的评价规则：累计预期增长量（cm）与偏小/偏大比例。"""

    expected_gain_cm: float
    small_ratio: float
    large_ratio: float


@dataclass(frozen=True)
class CohortRule:
    """群体评价规则：最少可测样本数与去掉的最短记录条数。"""

    min_measurable_count: int
    drop_shortest_count: int


@dataclass(frozen=True)
class WeightEstimation:
    """石斑鱼经验估重公式 `体重(g) = coefficient_a × 全长(cm) ^ exponent_b`。"""

    coefficient_a: float
    exponent_b: float


@dataclass(frozen=True)
class VideoCohortRule:
    """视频级评价规则：形成视频结论所需的最少可评价关键帧数。"""

    min_evaluable_frames: int


@dataclass(frozen=True)
class GrowthStandard:
    """养殖标准的内存表示（已通过 §10.5 全部校验）。"""

    schema_version: int
    cohort_rule: CohortRule
    video_cohort_rule: VideoCohortRule
    weight_estimation: WeightEstimation
    monthly_rules: Dict[int, MonthlyRule]


@dataclass(frozen=True)
class ReferenceRange:
    """当月综合参考全长及正常范围上下限，全部为未四舍五入的原始值（单位 cm）。"""

    culture_month: int
    stocking_avg_length_cm: float
    reference_length_cm: float
    small_lower_cm: float
    large_upper_cm: float


@dataclass(frozen=True)
class AssessmentContext:
    """一次评价的养殖参数：养殖月数（从投苗日起）与投苗时平均全长（cm）。

    任一项缺失即视为"不清楚月份"模式，可测鱼状态为"未评估"。
    """

    culture_month: Optional[int] = None
    stocking_avg_length_cm: Optional[float] = None

    def is_complete(self) -> bool:
        return self.culture_month is not None and self.stocking_avg_length_cm is not None


@dataclass(frozen=True)
class FishMeasurement:
    """单条鱼的测量输入：标识、是否可测、估算全长（cm）。"""

    id: str
    is_measurable: bool
    body_length_cm: float = 0.0

    def has_valid_length(self) -> bool:
        return self.is_measurable and self.body_length_cm > 0


@dataclass(frozen=True)
class EvaluatedFish:
    """单条鱼的评价结果：状态枚举与对应中文文案。"""

    id: str
    status: str
    status_text: str


@dataclass(frozen=True)
class GrowthEvaluation:
    """一次群体评价的完整产出，供图片首次识别与轻量重评共用。"""

    fish: List[EvaluatedFish] = field(default_factory=list)
    status_counts: Dict[str, int] = field(default_factory=dict)
    measurable_count: int = 0
    unmeasurable_count: int = 0
    trimmed_mean_length_cm: Optional[float] = None
    all_measurable_avg_length_cm: Optional[float] = None
    cohort_status: str = "unassessed"
    sample_sufficient: bool = False
    reference_range: Optional[ReferenceRange] = None
    advice: str = COHORT_ADVICE["unassessed"]


@dataclass(frozen=True)
class VideoGrowthEvaluation:
    """多关键帧视频的群体评价结果，不进行跨帧鱼只身份合并。"""

    frame_evaluations: List[GrowthEvaluation] = field(default_factory=list)
    video_length_cm: Optional[float] = None
    all_measurable_avg_length_cm: Optional[float] = None
    evaluable_frame_count: int = 0
    cohort_status: str = "unassessed"
    sample_sufficient: bool = False
    reference_range: Optional[ReferenceRange] = None
    advice: str = COHORT_ADVICE["unassessed"]


_cache_lock = threading.Lock()
_cache: Dict[str, GrowthStandard] = {}


def default_standard_path() -> str:
    """养殖标准默认路径：`backend/config/growth/grouper_growth_standard.json`。"""
    backend_root = Path(__file__).resolve().parents[2]
    return str(backend_root / "config" / "growth" / "grouper_growth_standard.json")


def load_growth_standard(path: Optional[str] = None) -> GrowthStandard:
    """读取并严格校验养殖标准，解析结果按路径在进程内缓存。

    参数 path 为空时依次取 `GROWTH_STANDARD_PATH` 环境配置和仓库默认路径。
    首次调用会读磁盘，之后命中缓存，因此**修改 JSON 后必须重启后端才生效**。
    文件缺失、JSON 非法或任一校验项不通过时抛 GrowthStandardError；调用方应据此
    降级为"未评估"而不是使用任何内置阈值。
    """
    resolved = str(Path(path or settings.GROWTH_STANDARD_PATH or default_standard_path()))
    cached = _cache.get(resolved)
    if cached is not None:
        return cached
    with _cache_lock:
        cached = _cache.get(resolved)
        if cached is None:
            cached = _parse_standard(_read_json(resolved))
            _cache[resolved] = cached
    return cached


def clear_growth_standard_cache() -> None:
    """清空进程内缓存（供测试在不同配置之间切换使用）。"""
    with _cache_lock:
        _cache.clear()


def calculate_reference_range(
    context: AssessmentContext,
    standard: Optional[GrowthStandard] = None,
) -> Optional[ReferenceRange]:
    """计算当月综合参考全长及正常范围上下限。

    口径：`综合参考全长 = 投苗时平均全长 + 该月累计预期增长量`，
    `偏小下限 = 综合参考全长 × small_ratio`、`偏大上限 = 综合参考全长 × large_ratio`。
    返回未四舍五入的原始值；月份或投苗体长缺失时返回 None（未评估模式）。
    月份不在第 3–15 个月内或投苗体长非正数时抛 GrowthStandardError。
    """
    if not context.is_complete():
        return None
    month = int(context.culture_month)  # type: ignore[arg-type]
    stocking = float(context.stocking_avg_length_cm)  # type: ignore[arg-type]
    rules = (standard or load_growth_standard()).monthly_rules
    rule = rules.get(month)
    if rule is None:
        raise GrowthStandardError(f"养殖月数 {month} 不在养殖标准覆盖范围内")
    if stocking <= 0:
        raise GrowthStandardError("投苗时平均全长必须大于 0")
    reference = stocking + rule.expected_gain_cm
    return ReferenceRange(
        culture_month=month,
        stocking_avg_length_cm=stocking,
        reference_length_cm=reference,
        small_lower_cm=reference * rule.small_ratio,
        large_upper_cm=reference * rule.large_ratio,
    )


def classify_growth_length(
    length_cm: float,
    reference_range: Optional[ReferenceRange],
) -> str:
    """对单条可测鱼做三档判断，全部使用未四舍五入的原始值比较。

    边界：`< 偏小下限` → small；`>= 偏小下限` 且 `<= 偏大上限` → normal；
    `> 偏大上限` → large。reference_range 为 None（未选月份或评价配置不可用）时
    返回 unassessed —— 它表示"能测但没评"，与"测不了"的 unmeasurable 不同。
    """
    if reference_range is None:
        return "unassessed"
    if length_cm < reference_range.small_lower_cm:
        return "small"
    if length_cm <= reference_range.large_upper_cm:
        return "normal"
    return "large"


def calculate_cohort_mean(
    lengths: Sequence[float],
    cohort_rule: Optional[CohortRule] = None,
) -> Optional[float]:
    """计算群体评价平均全长：排序后去掉最短的若干条，再对其余求平均。

    入参只应包含可测且体长有效的鱼。达不到 min_measurable_count 时返回 None
    （群体状态为"样本不足"），此时不去极端值也不给出群体分档；这条门槛的意义是
    样本太少时一条极端值就能左右结论，去极端反而更不稳。最短值并列时按
    drop_shortest_count 只去掉相应条数（当前为 1 条）。返回未四舍五入的原始值。
    """
    rule = cohort_rule or load_growth_standard().cohort_rule
    valid = sorted(float(value) for value in lengths if value > 0)
    if len(valid) < rule.min_measurable_count:
        return None
    kept = valid[rule.drop_shortest_count :]
    if not kept:
        return None
    return sum(kept) / len(kept)


def estimate_weight(
    length_cm: float,
    weight_estimation: Optional[WeightEstimation] = None,
) -> float:
    """按养殖标准的经验公式由全长估算体重（g），保留一位小数。

    非正数长度返回 0；公式系数来自养殖标准的 weight_estimation 段。
    """
    if length_cm <= 0:
        return 0.0
    formula = weight_estimation or load_growth_standard().weight_estimation
    return round(formula.coefficient_a * math.pow(length_cm, formula.exponent_b), 1)


def evaluate_growth_measurements(
    measurements: Sequence[FishMeasurement],
    context: AssessmentContext,
    standard: Optional[GrowthStandard] = None,
) -> GrowthEvaluation:
    """月度生长评价的唯一业务入口：图片首次识别与轻量重评都必须调用它。

    输入是已完成测长的单鱼列表（标识、可测性、估算全长 cm）与养殖参数
    （养殖月数、投苗时平均全长 cm）。输出个体状态、各状态计数、群体评价平均全长、
    全部可测鱼平均全长、群体状态和确定性管理建议。

    边界处理：不可测鱼不参与任何平均值；可测鱼数量不足 min_measurable_count 时
    群体状态为 insufficient（个体仍按月度规则分档）；养殖参数不全时个体与群体
    均为 unassessed。本函数不运行模型、不读图片、不写持久化；养殖标准非法时向上
    抛 GrowthStandardError，由端点决定降级方式。
    """
    resolved = standard or load_growth_standard()
    reference_range = calculate_reference_range(context, resolved)

    evaluated: List[EvaluatedFish] = []
    counts = {key: 0 for key in STATUS_TEXTS}
    measurable_lengths: List[float] = []
    for item in measurements:
        if item.has_valid_length():
            measurable_lengths.append(item.body_length_cm)
            status = classify_growth_length(item.body_length_cm, reference_range)
        elif item.is_measurable:
            # 标记为可测但长度无效（0 或负）：无法参与评价，按不可测处理
            status = "unmeasurable"
        else:
            status = "unmeasurable"
        counts[status] += 1
        evaluated.append(
            EvaluatedFish(id=item.id, status=status, status_text=STATUS_TEXTS[status])
        )

    trimmed_mean = calculate_cohort_mean(measurable_lengths, resolved.cohort_rule)
    all_measurable_avg = (
        sum(measurable_lengths) / len(measurable_lengths) if measurable_lengths else None
    )
    cohort_status = _resolve_cohort_status(trimmed_mean, reference_range)
    return GrowthEvaluation(
        fish=evaluated,
        status_counts=counts,
        measurable_count=len(measurable_lengths),
        unmeasurable_count=counts["unmeasurable"],
        trimmed_mean_length_cm=trimmed_mean,
        all_measurable_avg_length_cm=all_measurable_avg,
        cohort_status=cohort_status,
        sample_sufficient=trimmed_mean is not None,
        reference_range=reference_range,
        advice=COHORT_ADVICE[cohort_status],
    )


def evaluate_video_measurements(
    frame_measurements: Sequence[Sequence[FishMeasurement]],
    context: AssessmentContext,
    standard: Optional[GrowthStandard] = None,
) -> VideoGrowthEvaluation:
    """按帧评价视频，并以帧级评价全长的中位数形成视频级结论。

    每个关键帧独立复用 `evaluate_growth_measurements`，因此同一条鱼跨帧出现时
    仍按检测次数统计，不尝试推断独立鱼只身份。奇数帧取排序后的中间值，偶数帧
    取中间两个未四舍五入值的算术平均；显示层再负责格式化。函数不运行模型，
    养殖标准错误继续向端点抛出，由端点决定降级为未评估。
    """
    resolved = standard or load_growth_standard()
    frame_evaluations: List[GrowthEvaluation] = []
    all_lengths: List[float] = []
    for measurements in frame_measurements:
        evaluation = evaluate_growth_measurements(measurements, context, resolved)
        frame_evaluations.append(evaluation)
        all_lengths.extend(
            item.body_length_cm for item in measurements if item.has_valid_length()
        )

    frame_lengths = sorted(
        float(evaluation.trimmed_mean_length_cm)
        for evaluation in frame_evaluations
        if evaluation.trimmed_mean_length_cm is not None
    )
    video_length: Optional[float] = None
    if frame_lengths:
        middle = len(frame_lengths) // 2
        if len(frame_lengths) % 2:
            video_length = frame_lengths[middle]
        else:
            video_length = (frame_lengths[middle - 1] + frame_lengths[middle]) / 2

    reference_range = calculate_reference_range(context, resolved)
    evaluable_frame_count = len(frame_lengths)
    if reference_range is None:
        cohort_status = "unassessed"
    elif evaluable_frame_count < resolved.video_cohort_rule.min_evaluable_frames:
        cohort_status = "insufficient"
    else:
        cohort_status = classify_growth_length(video_length or 0.0, reference_range)

    return VideoGrowthEvaluation(
        frame_evaluations=frame_evaluations,
        video_length_cm=video_length,
        all_measurable_avg_length_cm=(
            sum(all_lengths) / len(all_lengths) if all_lengths else None
        ),
        evaluable_frame_count=evaluable_frame_count,
        cohort_status=cohort_status,
        sample_sufficient=(
            evaluable_frame_count >= resolved.video_cohort_rule.min_evaluable_frames
        ),
        reference_range=reference_range,
        advice=COHORT_ADVICE[cohort_status],
    )


def _resolve_cohort_status(
    trimmed_mean: Optional[float],
    reference_range: Optional[ReferenceRange],
) -> str:
    """群体状态：未选月份 → unassessed；可测样本不足 → insufficient；否则三档。"""
    if reference_range is None:
        return "unassessed"
    if trimmed_mean is None:
        return "insufficient"
    return classify_growth_length(trimmed_mean, reference_range)


# ---------------------------------------------------------------------------
# 解析与校验（方案 §10.5：任一项不通过即 fail fast）
# ---------------------------------------------------------------------------


def _read_json(path: str) -> Dict[str, object]:
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise GrowthStandardError(f"养殖标准文件不存在: {path}") from exc
    except json.JSONDecodeError as exc:
        raise GrowthStandardError(f"养殖标准 JSON 解析失败: {exc}") from exc
    if not isinstance(raw, dict):
        raise GrowthStandardError("养殖标准顶层必须是 JSON 对象")
    return raw


def _require_section(raw: Dict[str, object], name: str) -> Dict[str, object]:
    value = raw.get(name)
    if not isinstance(value, dict):
        raise GrowthStandardError(f"养殖标准段 {name!r} 必须是对象")
    return value


def _require_positive_float(raw: Dict[str, object], section: str, key: str) -> float:
    value = raw.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise GrowthStandardError(f"{section}.{key} 必须是数值")
    if float(value) <= 0:
        raise GrowthStandardError(f"{section}.{key} 必须大于 0")
    return float(value)


def _require_int(raw: Dict[str, object], section: str, key: str) -> int:
    value = raw.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise GrowthStandardError(f"{section}.{key} 必须是整数")
    return value


def _parse_standard(raw: Dict[str, object]) -> GrowthStandard:
    schema_version = _require_int(raw, "养殖标准", "schema_version")
    if schema_version != SUPPORTED_SCHEMA_VERSION:
        raise GrowthStandardError(
            f"不支持的养殖标准 schema_version={schema_version}，当前仅支持 {SUPPORTED_SCHEMA_VERSION}"
        )
    return GrowthStandard(
        schema_version=schema_version,
        cohort_rule=_parse_cohort_rule(_require_section(raw, "cohort_rule")),
        video_cohort_rule=_parse_video_cohort_rule(
            _require_section(raw, "video_cohort_rule")
        ),
        weight_estimation=_parse_weight_estimation(
            _require_section(raw, "weight_estimation")
        ),
        monthly_rules=_parse_monthly_rules(_require_section(raw, "monthly_rules")),
    )


def _parse_cohort_rule(raw: Dict[str, object]) -> CohortRule:
    minimum = _require_int(raw, "cohort_rule", "min_measurable_count")
    drop = _require_int(raw, "cohort_rule", "drop_shortest_count")
    if minimum < 3:
        raise GrowthStandardError("cohort_rule.min_measurable_count 不得低于 3")
    if drop < 0 or drop >= minimum:
        raise GrowthStandardError(
            "cohort_rule.drop_shortest_count 必须为非负数且小于 min_measurable_count"
        )
    return CohortRule(min_measurable_count=minimum, drop_shortest_count=drop)


def _parse_weight_estimation(raw: Dict[str, object]) -> WeightEstimation:
    return WeightEstimation(
        coefficient_a=_require_positive_float(raw, "weight_estimation", "coefficient_a"),
        exponent_b=_require_positive_float(raw, "weight_estimation", "exponent_b"),
    )


def _parse_monthly_rules(raw: Dict[str, object]) -> Dict[int, MonthlyRule]:
    """解析月度规则：月份必须为第 3–15 个月且不缺不重，增长量为正且不随月份下降。"""
    parsed: Dict[int, MonthlyRule] = {}
    for key, value in raw.items():
        try:
            month = int(str(key))
        except ValueError as exc:
            raise GrowthStandardError(f"monthly_rules 存在不可识别的月份键 {key!r}") from exc
        if month in parsed:
            raise GrowthStandardError(f"monthly_rules 月份 {month} 重复")
        if not isinstance(value, dict):
            raise GrowthStandardError(f"monthly_rules.{month} 必须是对象")
        section = f"monthly_rules.{month}"
        small_ratio = _require_positive_float(value, section, "small_ratio")
        large_ratio = _require_positive_float(value, section, "large_ratio")
        if small_ratio >= 1:
            raise GrowthStandardError(f"{section}.small_ratio 必须小于 1")
        if large_ratio <= 1:
            raise GrowthStandardError(f"{section}.large_ratio 必须大于 1")
        parsed[month] = MonthlyRule(
            expected_gain_cm=_require_positive_float(value, section, "expected_gain_cm"),
            small_ratio=small_ratio,
            large_ratio=large_ratio,
        )
    expected_months = list(range(FIRST_MONTH, LAST_MONTH + 1))
    missing = [month for month in expected_months if month not in parsed]
    if missing:
        raise GrowthStandardError(f"monthly_rules 缺少月份: {missing}")
    unexpected = sorted(month for month in parsed if month not in expected_months)
    if unexpected:
        raise GrowthStandardError(f"monthly_rules 存在超出第 3–15 个月的月份: {unexpected}")
    previous = 0.0
    for month in expected_months:
        gain = parsed[month].expected_gain_cm
        if gain < previous:
            raise GrowthStandardError(
                f"monthly_rules.{month}.expected_gain_cm 低于上一个月，累计增长量不得下降"
            )
        previous = gain
    return parsed


def _parse_video_cohort_rule(raw: Dict[str, object]) -> VideoCohortRule:
    """校验视频形成中位数结论所需的最少有效帧数。"""
    minimum = _require_int(raw, "video_cohort_rule", "min_evaluable_frames")
    if minimum < 3:
        raise GrowthStandardError("video_cohort_rule.min_evaluable_frames 不得低于 3")
    return VideoCohortRule(min_evaluable_frames=minimum)
