import type { GrowthCohortStatus, GrowthStatus } from '@/types/growth-monitoring'

/**
 * 全场统一的生长状态配色（方案 §7.2）。
 * 偏小=橙、正常=绿、偏大=蓝、样本不足=黄、未评估/不可测=灰、接口或配置错误=红。
 * 单鱼卡片、群体评估卡片和跨页摘要卡必须共用这里的映射，避免同一状态出现两种颜色。
 */
export type GrowthStatusTagType = 'primary' | 'success' | 'warning' | 'danger' | 'info'

/** 暂停展示偏小/正常/偏大状态字段；保留全部计算与映射，后续可直接恢复。 */
export const SHOW_GROWTH_STATUS_UI = false

export const GROWTH_STATUS_TAG_TYPE: Record<GrowthStatus, GrowthStatusTagType> = {
  small: 'warning',
  normal: 'success',
  large: 'primary',
  unassessed: 'info',
  unmeasurable: 'info'
}

export const GROWTH_COHORT_TAG_TYPE: Record<GrowthCohortStatus, GrowthStatusTagType> = {
  small: 'warning',
  normal: 'success',
  large: 'primary',
  insufficient: 'warning',
  unassessed: 'info'
}

/** 接口失败或评价配置不可用时的提示色 */
export const GROWTH_ERROR_TAG_TYPE: GrowthStatusTagType = 'danger'

export const GROWTH_COHORT_STATUS_LABEL: Record<GrowthCohortStatus, string> = {
  small: '偏小',
  normal: '正常',
  large: '偏大',
  insufficient: '样本不足',
  unassessed: '未评估'
}

/** 群体状态结论文案（方案 §7.3），页面直接展示，不再自行拼接 */
export const GROWTH_COHORT_STATUS_TEXT: Record<GrowthCohortStatus, string> = {
  small: '群体生长低于本月参考下限',
  normal: '群体生长处于本月正常参考范围',
  large: '群体生长高于本月正常参考范围',
  insufficient: '有效样本不足，暂不能判断群体生长状态',
  unassessed: '已完成体长测量，暂未进行月度生长评价'
}

/**
 * 单鱼状态的补充说明，用于解释“未评估”和“不可测”的业务差别：
 * 未评估 = 体长测量成功但没有月度评价依据；不可测 = 无法可靠测长，没有体长结果。
 */
export const GROWTH_STATUS_HINT: Partial<Record<GrowthStatus, string>> = {
  unassessed: '已完成体长测量，暂未进行月度生长评价',
  unmeasurable: '该鱼体无法可靠测长，不参与平均值与分档'
}

export const getGrowthStatusTagType = (status: GrowthStatus | null | undefined) =>
  status ? GROWTH_STATUS_TAG_TYPE[status] : 'info'

export const getGrowthCohortTagType = (status: GrowthCohortStatus | null | undefined) =>
  status ? GROWTH_COHORT_TAG_TYPE[status] : 'info'
