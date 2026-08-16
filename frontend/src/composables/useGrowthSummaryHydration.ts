import { onMounted, watch, type Ref } from 'vue'
import { getLatestGrowthRecord } from '@/api/growth-monitoring/records'
import {
  DEFAULT_GROWTH_POND_ID,
  useGrowthRecognitionStore,
  type LatestGrowthRecognitionInput
} from '@/store/modules/growth-recognition'
import type { GrowthRecordItem } from '@/types/growth-monitoring'

/**
 * 把数据库识别记录映射为跨页摘要结构。
 * validUntil 不传，由 store 按识别时间 +24h 计算，保持过期语义一致。
 */
const toSummary = (record: GrowthRecordItem): LatestGrowthRecognitionInput => ({
  pondId: record.pondId,
  sourceType: record.sourceType,
  sampleSource: record.sourceType === 'video' ? 'video-task' : 'user-upload',
  recordId: record.id,
  recordUpdatedAt: record.updatedAt ?? record.recognizedAt,
  recognizedAt: record.recognizedAt,
  detectedCount: record.detectedCount,
  measurableCount: record.measurableCount,
  unmeasurableCount: record.unmeasurableCount,
  measurableRatio:
    record.detectedCount > 0
      ? Math.round((record.measurableCount / record.detectedCount) * 100)
      : 0,
  small: record.small,
  normal: record.normal,
  large: record.large,
  avgBodyLengthCm: record.avgBodyLengthCm,
  avgWeightG: record.avgWeightG,
  isDemoData: false,
  plannedFrameCount: record.plannedFrameCount ?? undefined,
  completedFrameCount: record.completedFrameCount ?? undefined,
  evaluableFrameCount: record.evaluableFrameCount ?? undefined,
  detectionOccurrenceCount: record.detectionOccurrenceCount ?? undefined,
  measurableOccurrenceCount: record.measurableOccurrenceCount ?? undefined,
  cultureMonth: record.cultureMonth,
  stockingAvgLengthCm: record.stockingAvgLengthCm,
  referenceLengthCm: record.referenceLengthCm,
  smallThresholdCm: record.smallThresholdCm,
  largeThresholdCm: record.largeThresholdCm,
  trimmedMeanLengthCm: record.trimmedMeanLengthCm,
  allMeasurableAvgLengthCm: record.allMeasurableAvgLengthCm,
  cohortStatus: record.cohortStatus,
  advice: record.advice,
  perStatus: {
    small: record.small,
    normal: record.normal,
    large: record.large,
    unassessed: record.unassessed
  }
})

/**
 * 最近生长识别摘要的数据库兜底：
 * 本地 localStorage 缓存为空（清缓存/换浏览器）或数据库有更新的识别记录时，
 * 用 GET /growth/records/latest 恢复/刷新 store，跨页展示（投喂、驾驶舱）随之自动更新。
 * 请求失败静默降级，保留本地缓存展示。
 */
export function useGrowthSummaryHydration(pondId: Ref<string> | (() => string)) {
  const growthRecognitionStore = useGrowthRecognitionStore()

  const resolvePondId = () =>
    typeof pondId === 'function' ? pondId() || DEFAULT_GROWTH_POND_ID : pondId.value

  const hydrate = async () => {
    const targetPondId = resolvePondId()
    try {
      const record = await getLatestGrowthRecord(targetPondId)
      if (!record) return

      const local = growthRecognitionStore.getLatestSummary(targetPondId)
      // 本地已是同代或更新数据时不覆盖（本地摘要字段更全）
      if (
        local &&
        new Date(local.recordUpdatedAt ?? local.recognizedAt).getTime() >=
          new Date(record.updatedAt ?? record.recognizedAt).getTime()
      ) {
        return
      }

      growthRecognitionStore.setLatestSummary(toSummary(record))
    } catch (error) {
      console.warn('[Growth] 从数据库恢复最近识别摘要失败（保留本地缓存）:', error)
    }
  }

  onMounted(hydrate)
  if (typeof pondId !== 'function') {
    watch(pondId, hydrate)
  }

  return { hydrate }
}
