import { computed, onUnmounted, ref } from 'vue'
import {
  getGrowthVideoTask,
  uploadGrowthVideo
} from '@/api/growth-monitoring/detect'
import type {
  GrowthVideoDetectErrorCode,
  GrowthVideoDetectResultResponse,
  GrowthVideoFrameItem,
  GrowthVideoMeta,
  GrowthVideoTaskStatus
} from '@/types/growth-monitoring'

const POLL_INTERVAL = 2000

export function useGrowthVideoTask() {
  const growthVideoTaskId = ref<string | null>(null)
  const growthVideoTaskStatus = ref<GrowthVideoTaskStatus | null>(null)
  const growthVideoFrames = ref<GrowthVideoFrameItem[]>([])
  const selectedGrowthFrameId = ref<string | null>(null)
  const growthVideoPreviewUrl = ref<string | null>(null)
  const growthVideoAggregateStats = ref({
    small: 0,
    normal: 0,
    large: 0,
    detectedCount: 0
  })
  const growthVideoAggregateSummary = ref({
    avgBodyLengthCm: 0,
    avgWeightG: 0
  })
  const growthVideoMeta = ref<GrowthVideoMeta | null>(null)
  const growthVideoProgress = ref(0)
  const growthVideoErrorCode = ref<GrowthVideoDetectErrorCode | null>(null)

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

  const applyTaskResult = (result: GrowthVideoDetectResultResponse) => {
    growthVideoTaskId.value = result.taskId
    growthVideoTaskStatus.value = result.taskStatus
    growthVideoFrames.value = result.frames
    selectedGrowthFrameId.value = result.selectedFrameId
    growthVideoAggregateStats.value = result.aggregateStats
    growthVideoAggregateSummary.value = result.aggregateSummary
    growthVideoMeta.value = result.video
    growthVideoProgress.value = result.progress
    growthVideoErrorCode.value = result.errorCode
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
        stopPolling()
      }
    }, POLL_INTERVAL)
  }

  const uploadVideo = async (file: File) => {
    stopPolling()
    revokePreviewUrl()

    growthVideoPreviewUrl.value = URL.createObjectURL(file)
    growthVideoFrames.value = []
    selectedGrowthFrameId.value = null
    growthVideoAggregateStats.value = {
      small: 0,
      normal: 0,
      large: 0,
      detectedCount: 0
    }
    growthVideoAggregateSummary.value = {
      avgBodyLengthCm: 0,
      avgWeightG: 0
    }
    growthVideoMeta.value = {
      filename: file.name,
      durationSec: 0
    }
    growthVideoProgress.value = 0
    growthVideoErrorCode.value = null

    const created = await uploadGrowthVideo(file)
    growthVideoTaskId.value = created.taskId
    growthVideoTaskStatus.value = created.taskStatus
    schedulePoll()
  }

  const clearVideoTask = () => {
    stopPolling()
    revokePreviewUrl()
    growthVideoTaskId.value = null
    growthVideoTaskStatus.value = null
    growthVideoFrames.value = []
    selectedGrowthFrameId.value = null
    growthVideoAggregateStats.value = {
      small: 0,
      normal: 0,
      large: 0,
      detectedCount: 0
    }
    growthVideoAggregateSummary.value = {
      avgBodyLengthCm: 0,
      avgWeightG: 0
    }
    growthVideoMeta.value = null
    growthVideoProgress.value = 0
    growthVideoErrorCode.value = null
  }

  const markVideoTaskFailed = (errorCode: GrowthVideoDetectErrorCode) => {
    stopPolling()
    growthVideoTaskStatus.value = 'failed'
    growthVideoFrames.value = []
    selectedGrowthFrameId.value = null
    growthVideoAggregateStats.value = {
      small: 0,
      normal: 0,
      large: 0,
      detectedCount: 0
    }
    growthVideoAggregateSummary.value = {
      avgBodyLengthCm: 0,
      avgWeightG: 0
    }
    growthVideoProgress.value = 100
    growthVideoErrorCode.value = errorCode
  }

  const selectGrowthFrame = (frameId: string) => {
    selectedGrowthFrameId.value = frameId
  }

  const selectFrameDetection = (detectionId: string) => {
    const frame = selectedGrowthFrame.value
    if (!frame) return

    growthVideoFrames.value = growthVideoFrames.value.map((item) =>
      item.frameId === frame.frameId
        ? {
            ...item,
            selectedDetectionId: detectionId
          }
        : item
    )
  }

  onUnmounted(() => {
    clearVideoTask()
  })

  return {
    growthVideoTaskId,
    growthVideoTaskStatus,
    growthVideoFrames,
    selectedGrowthFrameId,
    growthVideoPreviewUrl,
    growthVideoAggregateStats,
    growthVideoAggregateSummary,
    growthVideoMeta,
    growthVideoProgress,
    growthVideoErrorCode,
    selectedGrowthFrame,
    uploadVideo,
    clearVideoTask,
    markVideoTaskFailed,
    selectGrowthFrame,
    selectFrameDetection,
    stopPolling
  }
}
