import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

export const DEFAULT_GROWTH_POND_ID = 'T001'
const DEFAULT_VALID_HOURS = 24
const LEGACY_DEFAULT_GROWTH_POND_IDS = ['pond-001']

export type GrowthRecognitionSourceType = 'image' | 'video'
export type GrowthRecognitionSampleSource = 'user-upload' | 'demo-data' | 'video-task'

export interface LatestGrowthRecognitionSummary {
  pondId: string
  sourceType: GrowthRecognitionSourceType
  sampleSource: GrowthRecognitionSampleSource
  taskId?: string
  recognizedAt: string
  validUntil: string
  detectedCount: number
  measurableCount: number
  unmeasurableCount: number
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

export const useGrowthRecognitionStore = defineStore(
  'growthRecognition',
  () => {
    const latestSummaryByPond = ref<Record<string, LatestGrowthRecognitionSummary>>({})

    const latestSummaries = computed(() => Object.values(latestSummaryByPond.value))

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
          small: normalizeCount(input.small),
          normal: normalizeCount(input.normal),
          large: normalizeCount(input.large),
          measurableRatio: Math.min(100, Math.max(0, measurableRatio)),
          avgBodyLengthCm: Number(input.avgBodyLengthCm ?? 0),
          avgWeightG: Number(input.avgWeightG ?? 0),
          isDemoData: Boolean(input.isDemoData)
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

    const clearLatestSummary = (pondId?: string) => {
      if (!pondId) {
        latestSummaryByPond.value = {}
        return
      }

      const next = { ...latestSummaryByPond.value }
      delete next[pondId]
      latestSummaryByPond.value = next
    }

    return {
      latestSummaryByPond,
      latestSummaries,
      setLatestSummary,
      getLatestSummary,
      isSummaryExpired,
      clearLatestSummary
    }
  },
  {
    persist: {
      key: 'growth-recognition',
      storage: localStorage
    }
  }
)
