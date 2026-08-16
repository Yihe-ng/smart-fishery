import { computed, onMounted, onUnmounted, ref } from 'vue'
import {
  cancelGrowthVideoTask,
  deleteGrowthVideoTask,
  getGrowthVideoTask,
  uploadGrowthVideoWithAssessment
} from '@/api/growth-monitoring/detect'
import type {
  GrowthAssessment,
  GrowthAssessmentParams,
  GrowthVideoDetectErrorCode,
  GrowthVideoDetectResultResponse,
  GrowthVideoFrameItem,
  GrowthVideoMeta,
  GrowthVideoTaskStage,
  GrowthVideoTaskStatus
} from '@/types/growth-monitoring'

const POLL_INTERVAL = 2000
const ACTIVE_TASK_STORAGE_KEY = 'growth-video-active-task'

interface ActiveVideoTaskSnapshot {
  taskId: string
  cultureMonth: number | null
  stockingAvgLengthCm: number | null
  createdAt: number
}

const createEmptyAggregateStats = () => ({
  small: 0,
  normal: 0,
  large: 0,
  unassessed: 0,
  detectedCount: 0,
  measurableCount: 0,
  unmeasurableCount: 0
})

const createEmptyAggregateSummary = () => ({ avgBodyLengthCm: 0, avgWeightG: 0 })

const readActiveTask = (): ActiveVideoTaskSnapshot | null => {
  try {
    const raw = sessionStorage.getItem(ACTIVE_TASK_STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as ActiveVideoTaskSnapshot
    return parsed.taskId ? parsed : null
  } catch {
    return null
  }
}

export function useGrowthVideoTask() {
  const growthVideoTaskId = ref<string | null>(null)
  const growthVideoTaskStatus = ref<GrowthVideoTaskStatus | null>(null)
  const growthVideoStage = ref<GrowthVideoTaskStage>('queued')
  const growthVideoFrames = ref<GrowthVideoFrameItem[]>([])
  const selectedGrowthFrameId = ref<string | null>(null)
  const growthVideoPreviewUrl = ref<string | null>(null)
  const growthVideoAggregateStats = ref(createEmptyAggregateStats())
  const growthVideoAggregateSummary = ref(createEmptyAggregateSummary())
  const growthVideoAssessment = ref<GrowthAssessment | null>(null)
  const growthVideoMeta = ref<GrowthVideoMeta | null>(null)
  const growthVideoProgress = ref(0)
  const growthVideoPlannedFrameCount = ref(0)
  const growthVideoCompletedFrameCount = ref(0)
  const growthVideoEvaluableFrameCount = ref(0)
  const growthVideoDetectionOccurrenceCount = ref(0)
  const growthVideoMeasurableOccurrenceCount = ref(0)
  const growthVideoIsPartial = ref(false)
  const growthVideoWarningCode = ref<string | null>(null)
  const growthVideoErrorCode = ref<GrowthVideoDetectErrorCode | null>(null)
  const growthVideoIsCancelling = ref(false)
  const restoredAssessmentParams = ref<GrowthAssessmentParams | null>(null)

  let pollTimer: number | null = null

  const selectedGrowthFrame = computed(
    () =>
      growthVideoFrames.value.find((item) => item.frameId === selectedGrowthFrameId.value) ?? null
  )

  const stopPolling = () => {
    if (pollTimer !== null) {
      window.clearTimeout(pollTimer)
      pollTimer = null
    }
  }

  const revokePreviewUrl = () => {
    if (growthVideoPreviewUrl.value) {
      URL.revokeObjectURL(growthVideoPreviewUrl.value)
      growthVideoPreviewUrl.value = null
    }
  }

  const clearActiveTaskStorage = () => {
    sessionStorage.removeItem(ACTIVE_TASK_STORAGE_KEY)
  }

  const saveActiveTaskStorage = (assessment?: GrowthAssessmentParams) => {
    if (!growthVideoTaskId.value) return
    const snapshot: ActiveVideoTaskSnapshot = {
      taskId: growthVideoTaskId.value,
      cultureMonth: assessment?.cultureMonth ?? null,
      stockingAvgLengthCm: assessment?.stockingAvgLengthCm ?? null,
      createdAt: Date.now()
    }
    sessionStorage.setItem(ACTIVE_TASK_STORAGE_KEY, JSON.stringify(snapshot))
  }

  const applyTaskResult = (result: GrowthVideoDetectResultResponse) => {
    growthVideoTaskId.value = result.taskId
    growthVideoTaskStatus.value = result.taskStatus
    growthVideoStage.value = result.stage
    growthVideoFrames.value = result.frames
    selectedGrowthFrameId.value = result.selectedFrameId
    growthVideoAggregateStats.value = result.aggregateStats
    growthVideoAggregateSummary.value = result.aggregateSummary
    growthVideoAssessment.value = result.assessment
    growthVideoMeta.value = result.video
    growthVideoProgress.value = result.progress
    growthVideoPlannedFrameCount.value = result.plannedFrameCount
    growthVideoCompletedFrameCount.value = result.completedFrameCount
    growthVideoEvaluableFrameCount.value = result.evaluableFrameCount
    growthVideoDetectionOccurrenceCount.value = result.detectionOccurrenceCount
    growthVideoMeasurableOccurrenceCount.value = result.measurableOccurrenceCount
    growthVideoIsPartial.value = result.isPartial
    growthVideoWarningCode.value = result.warningCode
    growthVideoErrorCode.value = result.errorCode

    if (
      result.taskStatus === 'success' ||
      result.taskStatus === 'failed' ||
      result.taskStatus === 'cancelled'
    ) {
      clearActiveTaskStorage()
      growthVideoIsCancelling.value = false
    }
  }

  const schedulePoll = () => {
    stopPolling()
    pollTimer = window.setTimeout(async () => {
      if (!growthVideoTaskId.value) return

      try {
        const result = await getGrowthVideoTask(growthVideoTaskId.value)
        applyTaskResult(result)

        if (result.taskStatus === 'queued' || result.taskStatus === 'processing') {
          schedulePoll()
        } else {
          stopPolling()
        }
      } catch {
        growthVideoTaskStatus.value = 'failed'
        growthVideoErrorCode.value = 'INTERNAL_ERROR'
        growthVideoIsCancelling.value = false
        stopPolling()
      }
    }, POLL_INTERVAL)
  }

  const uploadVideo = async (
    file: File,
    assessment?: GrowthAssessmentParams,
    storageAssessment: GrowthAssessmentParams | undefined = assessment
  ) => {
    stopPolling()
    revokePreviewUrl()
    clearActiveTaskStorage()

    growthVideoPreviewUrl.value = URL.createObjectURL(file)
    growthVideoFrames.value = []
    selectedGrowthFrameId.value = null
    growthVideoAssessment.value = null
    growthVideoAggregateStats.value = createEmptyAggregateStats()
    growthVideoAggregateSummary.value = createEmptyAggregateSummary()
    growthVideoMeta.value = { filename: file.name, durationSec: 0 }
    growthVideoProgress.value = 0
    growthVideoPlannedFrameCount.value = 0
    growthVideoCompletedFrameCount.value = 0
    growthVideoEvaluableFrameCount.value = 0
    growthVideoDetectionOccurrenceCount.value = 0
    growthVideoMeasurableOccurrenceCount.value = 0
    growthVideoIsPartial.value = false
    growthVideoWarningCode.value = null
    growthVideoErrorCode.value = null
    growthVideoIsCancelling.value = false

    const created = await uploadGrowthVideoWithAssessment(file, assessment)
    growthVideoTaskId.value = created.taskId
    growthVideoTaskStatus.value = created.taskStatus
    growthVideoStage.value = 'queued'
    saveActiveTaskStorage(storageAssessment)
    schedulePoll()
  }

  const restoreActiveTask = async () => {
    const snapshot = readActiveTask()
    if (!snapshot) return
    growthVideoTaskId.value = snapshot.taskId
    try {
      const result = await getGrowthVideoTask(snapshot.taskId)
      if (result.taskStatus === 'cancelled') {
        clearActiveTaskStorage()
        clearVideoTask({ clearActiveStorage: false })
        return
      }
      restoredAssessmentParams.value = {
        cultureMonth: snapshot.cultureMonth,
        stockingAvgLengthCm: snapshot.stockingAvgLengthCm
      }
      applyTaskResult(result)
      if (result.taskStatus === 'queued' || result.taskStatus === 'processing') schedulePoll()
    } catch {
      clearActiveTaskStorage()
      clearVideoTask({ clearActiveStorage: false })
    }
  }

  const cancelVideoTask = async () => {
    if (!growthVideoTaskId.value || !growthVideoTaskStatus.value) return
    if (!['queued', 'processing'].includes(growthVideoTaskStatus.value)) return
    growthVideoIsCancelling.value = true
    try {
      const result = await cancelGrowthVideoTask(growthVideoTaskId.value)
      // 后端接受取消后不再允许刷新恢复临时关键帧；当前页面仍继续轮询终态。
      clearActiveTaskStorage()
      applyTaskResult(result)
      if (result.taskStatus === 'queued' || result.taskStatus === 'processing') schedulePoll()
    } catch (error) {
      growthVideoIsCancelling.value = false
      schedulePoll()
      throw error
    }
  }

  const releaseVideoTask = async () => {
    const taskId = growthVideoTaskId.value
    if (!taskId) return
    clearVideoTask()
    await deleteGrowthVideoTask(taskId)
  }

  const clearVideoTask = ({ clearActiveStorage = true }: { clearActiveStorage?: boolean } = {}) => {
    stopPolling()
    revokePreviewUrl()
    if (clearActiveStorage) clearActiveTaskStorage()
    growthVideoTaskId.value = null
    growthVideoTaskStatus.value = null
    growthVideoStage.value = 'queued'
    growthVideoFrames.value = []
    selectedGrowthFrameId.value = null
    growthVideoAssessment.value = null
    growthVideoAggregateStats.value = createEmptyAggregateStats()
    growthVideoAggregateSummary.value = createEmptyAggregateSummary()
    growthVideoMeta.value = null
    growthVideoProgress.value = 0
    growthVideoPlannedFrameCount.value = 0
    growthVideoCompletedFrameCount.value = 0
    growthVideoEvaluableFrameCount.value = 0
    growthVideoDetectionOccurrenceCount.value = 0
    growthVideoMeasurableOccurrenceCount.value = 0
    growthVideoIsPartial.value = false
    growthVideoWarningCode.value = null
    growthVideoErrorCode.value = null
    growthVideoIsCancelling.value = false
  }

  const markVideoTaskFailed = (errorCode: GrowthVideoDetectErrorCode) => {
    stopPolling()
    clearActiveTaskStorage()
    growthVideoTaskStatus.value = 'failed'
    growthVideoFrames.value = []
    selectedGrowthFrameId.value = null
    growthVideoAssessment.value = null
    growthVideoAggregateStats.value = createEmptyAggregateStats()
    growthVideoAggregateSummary.value = createEmptyAggregateSummary()
    growthVideoPlannedFrameCount.value = 0
    growthVideoCompletedFrameCount.value = 0
    growthVideoEvaluableFrameCount.value = 0
    growthVideoDetectionOccurrenceCount.value = 0
    growthVideoMeasurableOccurrenceCount.value = 0
    growthVideoIsPartial.value = false
    growthVideoWarningCode.value = null
    growthVideoProgress.value = 100
    growthVideoErrorCode.value = errorCode
    growthVideoIsCancelling.value = false
  }

  const selectGrowthFrame = (frameId: string) => {
    selectedGrowthFrameId.value = frameId
  }

  const selectFrameDetection = (detectionId: string) => {
    const frame = selectedGrowthFrame.value
    if (!frame) return
    growthVideoFrames.value = growthVideoFrames.value.map((item) =>
      item.frameId === frame.frameId ? { ...item, selectedDetectionId: detectionId } : item
    )
  }

  onMounted(() => {
    void restoreActiveTask()
  })

  onUnmounted(() => {
    // 任务状态保存在 sessionStorage，离开页面后停止轮询但不取消后端任务。
    stopPolling()
    revokePreviewUrl()
  })

  return {
    growthVideoTaskId,
    growthVideoTaskStatus,
    growthVideoStage,
    growthVideoFrames,
    selectedGrowthFrameId,
    growthVideoPreviewUrl,
    growthVideoAggregateStats,
    growthVideoAggregateSummary,
    growthVideoAssessment,
    growthVideoMeta,
    growthVideoProgress,
    growthVideoPlannedFrameCount,
    growthVideoCompletedFrameCount,
    growthVideoEvaluableFrameCount,
    growthVideoDetectionOccurrenceCount,
    growthVideoMeasurableOccurrenceCount,
    growthVideoIsPartial,
    growthVideoWarningCode,
    growthVideoErrorCode,
    growthVideoIsCancelling,
    restoredAssessmentParams,
    selectedGrowthFrame,
    uploadVideo,
    cancelVideoTask,
    releaseVideoTask,
    clearVideoTask,
    markVideoTaskFailed,
    selectGrowthFrame,
    selectFrameDetection,
    stopPolling
  }
}
