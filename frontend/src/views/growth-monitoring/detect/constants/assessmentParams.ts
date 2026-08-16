/** 养殖月数下拉的“不清楚，仅测量体长”选项值；用 0 与真实月份 3–15 区分 */
export const UNKNOWN_CULTURE_MONTH = 0

export type CultureMonthSelection = number | null

export const MIN_CULTURE_MONTH = 3
export const MAX_CULTURE_MONTH = 15

export const MONTH_OPTIONS = Array.from(
  { length: MAX_CULTURE_MONTH - MIN_CULTURE_MONTH + 1 },
  (_, index) => MIN_CULTURE_MONTH + index
)

export const MIN_STOCKING_LENGTH_CM = 1
export const MAX_STOCKING_LENGTH_CM = 100

export interface GrowthAssessmentErrors {
  cultureMonth?: string
  stockingAvgLengthCm?: string
}

export const isKnownCultureMonth = (value: CultureMonthSelection): value is number =>
  typeof value === 'number' &&
  value >= MIN_CULTURE_MONTH &&
  value <= MAX_CULTURE_MONTH

/**
 * 投苗平均全长有效性：1.0–100.0 cm，允许一位小数。
 * 超范围或非数值都视为无效，交由上传前校验拦截。
 */
export const isValidStockingLength = (value: number | null): value is number =>
  typeof value === 'number' &&
  Number.isFinite(value) &&
  value >= MIN_STOCKING_LENGTH_CM &&
  value <= MAX_STOCKING_LENGTH_CM

export const formatLengthCm = (value: number | null | undefined) =>
  typeof value === 'number' && Number.isFinite(value) ? value.toFixed(1) : '--'
