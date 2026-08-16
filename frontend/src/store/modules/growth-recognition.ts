import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import type { GrowthCohortStatus } from '@/types/growth-monitoring'

export const DEFAULT_GROWTH_POND_ID = 'T001'
const DEFAULT_VALID_HOURS = 24
const LEGACY_DEFAULT_GROWTH_POND_IDS = ['pond-001']

export type GrowthRecognitionSourceType = 'image' | 'video'
export type GrowthRecognitionSampleSource = 'user-upload' | 'demo-data' | 'video-task'

/** 摘要中的个体状态分布，用于跨页展示，不含单鱼明细 */
export interface GrowthRecognitionPerStatus {
  small: number
  normal: number
  large: number
  unassessed: number
}

export interface LatestGrowthRecognitionSummary {
  pondId: string
  sourceType: GrowthRecognitionSourceType
  sampleSource: GrowthRecognitionSampleSource
  taskId?: string
  /** 摘要落库后回写的数据库记录 id；轻量重评按此 id 更新记录而不是新增历史行 */
  recordId?: number
  /** 数据库记录更新时间，用于跨标签页/浏览器判断评价是否已刷新 */
  recordUpdatedAt?: string
  recognizedAt: string
  validUntil: string
  detectedCount: number
  measurableCount: number
  unmeasurableCount: number
  /** 视频任务的关键帧口径；图片摘要不填写。 */
  plannedFrameCount?: number
  completedFrameCount?: number
  evaluableFrameCount?: number
  detectionOccurrenceCount?: number
  measurableOccurrenceCount?: number
  measurableRatio: number
  avgBodyLengthCm: number
  avgWeightG: number
  small: number
  normal: number
  large: number
  avgConfidence?: number
  scaleCmPerPixel?: number
  algorithmVersion?: string
  isDemoData: boolean
  /** 养殖月数（从投苗日起）；未选择月份时为 null */
  cultureMonth?: number | null
  /** 投苗时平均全长（cm） */
  stockingAvgLengthCm?: number | null
  /** 当月综合参考全长（cm） */
  referenceLengthCm?: number | null
  /** 偏小下限（cm） */
  smallThresholdCm?: number | null
  /** 偏大上限（cm） */
  largeThresholdCm?: number | null
  /** 群体评价平均全长（cm），已去掉一条极端值 */
  trimmedMeanLengthCm?: number | null
  /** 全部可测鱼平均全长（cm） */
  allMeasurableAvgLengthCm?: number | null
  cohortStatus?: GrowthCohortStatus | null
  /** 后端确定性规则生成的管理建议，不含具体投喂克数 */
  advice?: string | null
  perStatus?: GrowthRecognitionPerStatus
}

/** 上传前记忆的养殖参数，独立于 24 小时摘要有效期，长期保留在本浏览器 */
export interface GrowthRecentParams {
  cultureMonth: number | null
  stockingAvgLengthCm: number | null
}

export type LatestGrowthRecognitionInput = Omit<
  LatestGrowthRecognitionSummary,
  'recognizedAt' | 'validUntil' | 'measurableRatio'
> &
  Partial<Pick<LatestGrowthRecognitionSummary, 'recognizedAt' | 'validUntil' | 'measurableRatio'>>

const addHours = (date: Date, hours: number) => {
  const next = new Date(date)
  next.setHours(next.getHours() + hours)
  return next
}

const normalizeCount = (value: number | undefined) => Math.max(0, Number(value ?? 0))

const normalizeOptionalNumber = (value: number | null | undefined) =>
  typeof value === 'number' && Number.isFinite(value) ? value : null

export const useGrowthRecognitionStore = defineStore(
  'growthRecognition',
  () => {
    const latestSummaryByPond = ref<Record<string, LatestGrowthRecognitionSummary>>({})
    const recentParams = ref<GrowthRecentParams>({
      cultureMonth: null,
      stockingAvgLengthCm: null
    })

    const latestSummaries = computed(() => Object.values(latestSummaryByPond.value))

    /**
     * 写入某个池塘“最近一次成功识别”摘要，并按 24 小时给出有效期。
     * 只保存跨页展示需要的统计与评价字段；不保存图片 Base64、掩码和检测框数组，
     * 因为 localStorage 容量有限且这些大对象无法安全序列化。
     * 调用方必须只在识别或重评成功时调用：识别失败与重评失败都不能覆盖上一次成功摘要。
     * 副作用：更新持久化的 localStorage（persist key `growth-recognition`）。
     */
    const setLatestSummary = (input: LatestGrowthRecognitionInput) => {
      const recognizedAtDate = input.recognizedAt ? new Date(input.recognizedAt) : new Date()
      const recognizedAt = Number.isNaN(recognizedAtDate.getTime())
        ? new Date().toISOString()
        : recognizedAtDate.toISOString()
      const validUntil =
        input.validUntil ?? addHours(new Date(recognizedAt), DEFAULT_VALID_HOURS).toISOString()

      const detectedCount = normalizeCount(input.detectedCount)
      const measurableCount = normalizeCount(input.measurableCount)
      const measurableRatio =
        typeof input.measurableRatio === 'number'
          ? input.measurableRatio
          : detectedCount > 0
            ? Math.round((measurableCount / detectedCount) * 100)
            : 0

      const nextSummaries = {
        ...latestSummaryByPond.value,
        [input.pondId]: {
          ...input,
          recognizedAt,
          validUntil,
          detectedCount,
          measurableCount,
          unmeasurableCount: normalizeCount(input.unmeasurableCount),
          plannedFrameCount:
            input.plannedFrameCount === undefined
              ? undefined
              : normalizeCount(input.plannedFrameCount),
          completedFrameCount:
            input.completedFrameCount === undefined
              ? undefined
              : normalizeCount(input.completedFrameCount),
          evaluableFrameCount:
            input.evaluableFrameCount === undefined
              ? undefined
              : normalizeCount(input.evaluableFrameCount),
          detectionOccurrenceCount:
            input.detectionOccurrenceCount === undefined
              ? undefined
              : normalizeCount(input.detectionOccurrenceCount),
          measurableOccurrenceCount:
            input.measurableOccurrenceCount === undefined
              ? undefined
              : normalizeCount(input.measurableOccurrenceCount),
          small: normalizeCount(input.small),
          normal: normalizeCount(input.normal),
          large: normalizeCount(input.large),
          measurableRatio: Math.min(100, Math.max(0, measurableRatio)),
          avgBodyLengthCm: Number(input.avgBodyLengthCm ?? 0),
          avgWeightG: Number(input.avgWeightG ?? 0),
          isDemoData: Boolean(input.isDemoData),
          cultureMonth: normalizeOptionalNumber(input.cultureMonth),
          stockingAvgLengthCm: normalizeOptionalNumber(input.stockingAvgLengthCm),
          referenceLengthCm: normalizeOptionalNumber(input.referenceLengthCm),
          smallThresholdCm: normalizeOptionalNumber(input.smallThresholdCm),
          largeThresholdCm: normalizeOptionalNumber(input.largeThresholdCm),
          trimmedMeanLengthCm: normalizeOptionalNumber(input.trimmedMeanLengthCm),
          allMeasurableAvgLengthCm: normalizeOptionalNumber(input.allMeasurableAvgLengthCm),
          cohortStatus: input.cohortStatus ?? null,
          advice: input.advice ?? null,
          perStatus: input.perStatus ?? {
            small: normalizeCount(input.small),
            normal: normalizeCount(input.normal),
            large: normalizeCount(input.large),
            unassessed: 0
          }
        }
      }

      if (input.pondId === DEFAULT_GROWTH_POND_ID) {
        LEGACY_DEFAULT_GROWTH_POND_IDS.forEach((legacyPondId) => {
          delete nextSummaries[legacyPondId]
        })
      }

      latestSummaryByPond.value = nextSummaries
    }

    const getLatestSummary = (pondId?: string) => {
      const targetPondId = pondId || DEFAULT_GROWTH_POND_ID
      const exactSummary = latestSummaryByPond.value[targetPondId]

      if (exactSummary) {
        return exactSummary
      }

      if (targetPondId === DEFAULT_GROWTH_POND_ID) {
        const legacyPondId = LEGACY_DEFAULT_GROWTH_POND_IDS.find(
          (item) => latestSummaryByPond.value[item]
        )

        return legacyPondId ? latestSummaryByPond.value[legacyPondId] : null
      }

      return null
    }

    const isSummaryExpired = (summary: LatestGrowthRecognitionSummary | null) => {
      if (!summary) return false
      return new Date(summary.validUntil).getTime() < Date.now()
    }

    /** 摘要落库成功后回写数据库记录 id，供后续轻量重评按记录更新 */
    const setRecordId = (pondId: string, recordId: number) => {
      const summary = latestSummaryByPond.value[pondId]
      if (!summary) return
      latestSummaryByPond.value = {
        ...latestSummaryByPond.value,
        [pondId]: { ...summary, recordId }
      }
    }

    /** 只清除识别摘要；已记忆的养殖参数（recentParams）按方案 §5.2 必须保留 */
    const clearLatestSummary = (pondId?: string) => {
      if (!pondId) {
        latestSummaryByPond.value = {}
        return
      }

      const next = { ...latestSummaryByPond.value }
      delete next[pondId]
      latestSummaryByPond.value = next
    }

    /**
     * 记住最近一次校验通过的养殖月数与投苗平均全长。
     * 仅在参数校验通过、准备进入图片选择流程时调用，避免把无效输入写进记忆。
     * 该记忆不设有效期，也不随“清空结果”被清除。
     */
    const setRecentParams = (params: Partial<GrowthRecentParams>) => {
      recentParams.value = {
        cultureMonth:
          params.cultureMonth === undefined
            ? recentParams.value.cultureMonth
            : normalizeOptionalNumber(params.cultureMonth),
        stockingAvgLengthCm:
          params.stockingAvgLengthCm === undefined
            ? recentParams.value.stockingAvgLengthCm
            : normalizeOptionalNumber(params.stockingAvgLengthCm)
      }
    }

    const clearRecentParams = () => {
      recentParams.value = { cultureMonth: null, stockingAvgLengthCm: null }
    }

    return {
      latestSummaryByPond,
      latestSummaries,
      recentParams,
      setLatestSummary,
      getLatestSummary,
      isSummaryExpired,
      setRecordId,
      clearLatestSummary,
      setRecentParams,
      clearRecentParams
    }
  },
  {
    persist: {
      key: 'growth-recognition',
      storage: localStorage
    }
  }
)
