import {
  saveGrowthRecord,
  updateGrowthRecordAssessment
} from '@/api/growth-monitoring/records'
import {
  useGrowthRecognitionStore,
  type LatestGrowthRecognitionSummary
} from '@/store/modules/growth-recognition'

/**
 * 识别结果落库同步（fire-and-forget）：
 * - 演示数据不入库；
 * - 失败只 console.warn，不弹错误提示、不影响识别结果展示；
 * - 落库成功后回写 recordId 到摘要 store，轻量重评按记录更新而不是新增历史行。
 */
export function useGrowthRecordSync() {
  const growthRecognitionStore = useGrowthRecognitionStore()

  const toSavePayload = (summary: LatestGrowthRecognitionSummary) => ({
    pondId: summary.pondId,
    sourceType: summary.sourceType,
    recognizedAt: summary.recognizedAt,
    detectedCount: summary.detectedCount,
    measurableCount: summary.measurableCount,
    unmeasurableCount: summary.unmeasurableCount,
    small: summary.small,
    normal: summary.normal,
    large: summary.large,
    unassessed: summary.perStatus?.unassessed ?? 0,
    plannedFrameCount: summary.plannedFrameCount,
    completedFrameCount: summary.completedFrameCount,
    evaluableFrameCount: summary.evaluableFrameCount,
    detectionOccurrenceCount: summary.detectionOccurrenceCount,
    measurableOccurrenceCount: summary.measurableOccurrenceCount,
    cultureMonth: summary.cultureMonth ?? null,
    stockingAvgLengthCm: summary.stockingAvgLengthCm ?? null,
    avgBodyLengthCm: summary.avgBodyLengthCm,
    avgWeightG: summary.avgWeightG,
    referenceLengthCm: summary.referenceLengthCm ?? null,
    smallThresholdCm: summary.smallThresholdCm ?? null,
    largeThresholdCm: summary.largeThresholdCm ?? null,
    trimmedMeanLengthCm: summary.trimmedMeanLengthCm ?? null,
    allMeasurableAvgLengthCm: summary.allMeasurableAvgLengthCm ?? null,
    cohortStatus: summary.cohortStatus ?? null,
    advice: summary.advice ?? null
  })

  /** 识别成功后保存新记录 */
  const syncRecord = (summary: LatestGrowthRecognitionSummary) => {
    if (summary.isDemoData) return

    void saveGrowthRecord(toSavePayload(summary))
      .then((record) => {
        growthRecognitionStore.setRecordId(summary.pondId, record.id)
      })
      .catch((error) => {
        console.warn('[Growth] 识别记录落库失败（不影响识别展示）:', error)
      })
  }

  /** 轻量重评成功后更新已有记录的评价字段；旧摘要没有 recordId 时退化为新增 */
  const syncReevaluated = (summary: LatestGrowthRecognitionSummary) => {
    if (summary.isDemoData) return

    if (!summary.recordId) {
      syncRecord(summary)
      return
    }

    void updateGrowthRecordAssessment(summary.recordId, {
      cultureMonth: summary.cultureMonth ?? null,
      stockingAvgLengthCm: summary.stockingAvgLengthCm ?? null,
      referenceLengthCm: summary.referenceLengthCm ?? null,
      smallThresholdCm: summary.smallThresholdCm ?? null,
      largeThresholdCm: summary.largeThresholdCm ?? null,
      trimmedMeanLengthCm: summary.trimmedMeanLengthCm ?? null,
      allMeasurableAvgLengthCm: summary.allMeasurableAvgLengthCm ?? null,
      cohortStatus: summary.cohortStatus ?? null,
      advice: summary.advice ?? null
    }).catch((error) => {
      console.warn('[Growth] 重评记录更新失败（不影响识别展示）:', error)
    })
  }

  return { syncRecord, syncReevaluated }
}
