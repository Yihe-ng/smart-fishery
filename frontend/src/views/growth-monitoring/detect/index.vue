<template>
  <div class="growth-monitoring-detect">
    <div class="page-header">
      <div class="title-section">
        <ArtSvgIcon icon="ri:scales-3-line" style="font-size: 32px; color: #409eff" />
        <h2>智能鱼类生长识别系统</h2>
      </div>
      <el-tag :type="headerStatus.type" size="large" effect="dark">
        {{ headerStatus.text }}
      </el-tag>
    </div>

    <el-row :gutter="20">
      <el-col :xs="24" :sm="24" :md="8" :lg="6">
        <GrowthStatsSummary :stats="activeStats" />
        <GrowthResultCard :result="activeDetection" :empty-text="resultEmptyText" />
        <GrowthDetectionList
          :detections="activeDetections"
          :selected-id="activeSelectedDetectionId"
          @select="handleSelectDetection"
        />
      </el-col>

      <el-col :xs="24" :sm="24" :md="16" :lg="18">
        <GrowthImageDisplay
          :image="activeImage"
          :detections="activeDetections"
          :selected-id="activeSelectedDetectionId"
          :task-status="displayTaskStatus"
          :error-message="activeErrorMessage"
          class="mb-4"
          @select="handleSelectDetection"
          @clear="handleClear"
        />

        <GrowthVideoTaskState
          v-if="inputMode === 'growthVideo'"
          :task-status="growthVideoTaskStatus"
          :progress="growthVideoProgress"
          :filename="growthVideoMeta?.filename"
          :frame-count="growthVideoFrames.length"
          :aggregate-stats="growthVideoAggregateStats"
          :error-message="activeErrorMessage"
        />

        <GrowthVideoFrameStrip
          v-if="inputMode === 'growthVideo' && growthVideoTaskStatus === 'success'"
          :frames="growthVideoFrames"
          :selected-frame-id="selectedGrowthFrameId"
          @select="handleSelectFrame"
        />

        <GrowthActionButtons
          :processing="isProcessing"
          :has-image="hasVisualResult"
          @upload-image="handleImageUpload"
          @upload-video="handleVideoUpload"
          @clear="handleClear"
        />
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
  import { computed, onUnmounted, ref, watch } from 'vue'
  import { ElMessage } from 'element-plus'
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import { detectGrowth } from '@/api/growth-monitoring/detect'
  import { loadingService } from '@/utils/ui'
  import type {
    GrowthDetectErrorCode,
    GrowthDetectResponse,
    GrowthDetectionItem,
    GrowthImageMeta,
    GrowthStats,
    GrowthTaskStatus,
    GrowthVideoDetectErrorCode
  } from '@/types/growth-monitoring'
  import GrowthActionButtons from './components/GrowthActionButtons.vue'
  import GrowthDetectionList from './components/GrowthDetectionList.vue'
  import GrowthImageDisplay from './components/GrowthImageDisplay.vue'
  import GrowthResultCard from './components/GrowthResultCard.vue'
  import GrowthStatsSummary from './components/GrowthStatsSummary.vue'
  import GrowthVideoFrameStrip from './components/GrowthVideoFrameStrip.vue'
  import GrowthVideoTaskState from './components/GrowthVideoTaskState.vue'
  import { useGrowthVideoTask } from './composables/useGrowthVideoTask'

  defineOptions({ name: 'GrowthMonitoringDetect' })

  type InputMode = 'image' | 'growthVideo'

  const EMPTY_STATS: GrowthStats = {
    small: 0,
    normal: 0,
    large: 0,
    detectedCount: 0
  }

  const inputMode = ref<InputMode>('image')
  const taskStatus = ref<GrowthTaskStatus>('idle')
  const imageMeta = ref<GrowthImageMeta | null>(null)
  const detections = ref<GrowthDetectionItem[]>([])
  const selectedDetectionId = ref<string | null>(null)
  const stats = ref<GrowthStats>({ ...EMPTY_STATS })
  const errorCode = ref<GrowthDetectErrorCode | null>(null)
  const errorMessage = ref('')

  const {
    growthVideoTaskStatus,
    growthVideoFrames,
    selectedGrowthFrameId,
    growthVideoAggregateStats,
    growthVideoMeta,
    growthVideoProgress,
    growthVideoErrorCode,
    selectedGrowthFrame,
    uploadVideo,
    clearVideoTask,
    markVideoTaskFailed,
    selectGrowthFrame,
    selectFrameDetection
  } = useGrowthVideoTask()

  const imageSelectedDetection = computed(
    () => detections.value.find((item) => item.id === selectedDetectionId.value) ?? null
  )

  const activeImage = computed(() =>
    inputMode.value === 'growthVideo' ? selectedGrowthFrame.value?.image ?? null : imageMeta.value
  )

  const activeDetections = computed(() =>
    inputMode.value === 'growthVideo' ? selectedGrowthFrame.value?.detections ?? [] : detections.value
  )

  const activeSelectedDetectionId = computed(() =>
    inputMode.value === 'growthVideo'
      ? selectedGrowthFrame.value?.selectedDetectionId ?? null
      : selectedDetectionId.value
  )

  const activeDetection = computed(() =>
    inputMode.value === 'growthVideo'
      ? selectedGrowthFrame.value?.detections.find(
          (item) => item.id === selectedGrowthFrame.value?.selectedDetectionId
        ) ?? null
      : imageSelectedDetection.value
  )

  const activeStats = computed(() =>
    inputMode.value === 'growthVideo' ? selectedGrowthFrame.value?.stats ?? EMPTY_STATS : stats.value
  )

  const displayTaskStatus = computed<GrowthTaskStatus>(() => {
    if (inputMode.value === 'growthVideo') {
      if (growthVideoTaskStatus.value === 'queued' || growthVideoTaskStatus.value === 'processing') {
        return 'processing'
      }
      if (growthVideoTaskStatus.value === 'failed') {
        return 'failed'
      }
      if (growthVideoTaskStatus.value === 'success') {
        return 'success'
      }
      return 'idle'
    }

    return taskStatus.value === 'uploading' ? 'processing' : taskStatus.value
  })

  const isProcessing = computed(
    () =>
      taskStatus.value === 'uploading' ||
      taskStatus.value === 'processing' ||
      growthVideoTaskStatus.value === 'queued' ||
      growthVideoTaskStatus.value === 'processing'
  )

  const hasVisualResult = computed(
    () =>
      Boolean(activeImage.value?.src) ||
      Boolean(imageMeta.value?.src) ||
      Boolean(selectedGrowthFrame.value?.image.src) ||
      inputMode.value === 'growthVideo'
  )

  const headerStatus = computed(() => {
    switch (displayTaskStatus.value) {
      case 'processing':
        return { type: 'warning' as const, text: '识别处理中' }
      case 'success':
        return { type: 'success' as const, text: '识别完成' }
      case 'failed':
        return { type: 'danger' as const, text: '识别失败' }
      default:
        return { type: 'info' as const, text: '系统待命' }
    }
  })

  const activeErrorMessage = computed(() => {
    if (inputMode.value === 'growthVideo') {
      return mapVideoErrorMessage(growthVideoErrorCode.value)
    }
    return errorMessage.value
  })

  const resultEmptyText = computed(() => {
    if (displayTaskStatus.value === 'success' && activeImage.value && !activeDetections.value.length) {
      return inputMode.value === 'growthVideo'
        ? '当前关键帧未识别到石斑鱼'
        : '未识别到石斑鱼'
    }
    if (displayTaskStatus.value === 'failed') {
      return activeErrorMessage.value || '识别失败，请重新上传素材'
    }
    return inputMode.value === 'growthVideo'
      ? '上传视频后可查看当前关键帧的识别详情'
      : '上传图片后可查看识别详情'
  })

  const resetImageState = () => {
    taskStatus.value = 'idle'
    imageMeta.value = null
    detections.value = []
    selectedDetectionId.value = null
    stats.value = { ...EMPTY_STATS }
    errorCode.value = null
    errorMessage.value = ''
  }

  const resetAllState = () => {
    inputMode.value = 'image'
    resetImageState()
    clearVideoTask()
  }

  const mapImageErrorMessage = (code: GrowthDetectErrorCode | null) => {
    switch (code) {
      case 'INVALID_IMAGE':
        return '图片格式无效，请重新上传。'
      case 'IMAGE_TOO_LARGE':
        return '图片过大，请压缩后重试。'
      case 'IMAGE_DECODE_FAILED':
        return '图片解析失败，请更换图片。'
      case 'MODEL_INFERENCE_FAILED':
        return '模型推理失败，请稍后重试。'
      case 'INTERNAL_ERROR':
        return '系统异常，请稍后重试。'
      case 'NO_FISH_DETECTED':
        return '未识别到石斑鱼'
      default:
        return '识别失败，请稍后重试。'
    }
  }

  const mapVideoErrorMessage = (code: GrowthVideoDetectErrorCode | null) => {
    switch (code) {
      case 'INVALID_VIDEO':
        return '视频格式无效，请重新上传。'
      case 'VIDEO_TOO_LARGE':
        return '视频过大，请压缩后重试。'
      case 'VIDEO_DECODE_FAILED':
        return '视频解析失败，请更换视频。'
      case 'NO_VALID_FRAMES':
        return '未提取到有效关键帧，请尝试更清晰的视频。'
      case 'MODEL_INFERENCE_FAILED':
        return '模型推理失败，请稍后重试。'
      case 'INTERNAL_ERROR':
        return '系统异常，请稍后重试。'
      default:
        return ''
    }
  }

  const applyDetectResponse = (response: GrowthDetectResponse) => {
    taskStatus.value = response.taskStatus
    imageMeta.value = response.image
    detections.value = response.detections
    selectedDetectionId.value = response.selectedDetectionId
    stats.value = response.stats
    errorCode.value = response.errorCode
    errorMessage.value = mapImageErrorMessage(response.errorCode)
  }

  const handleImageUpload = async (imgData: string) => {
    clearVideoTask()
    inputMode.value = 'image'
    taskStatus.value = 'uploading'
    imageMeta.value = {
      src: imgData,
      width: 0,
      height: 0
    }
    detections.value = []
    selectedDetectionId.value = null
    stats.value = { ...EMPTY_STATS }
    errorCode.value = null
    errorMessage.value = ''

    try {
      taskStatus.value = 'processing'
      const result = await detectGrowth(imgData)
      applyDetectResponse(result)

      if (result.errorCode === 'NO_FISH_DETECTED') {
        ElMessage.warning('未识别到石斑鱼')
      } else {
        ElMessage.success('图片识别完成')
      }
    } catch (error: any) {
      taskStatus.value = 'failed'
      detections.value = []
      selectedDetectionId.value = null
      stats.value = { ...EMPTY_STATS }

      const rawMessage = String(error?.message || '')
      const matchedCode = (
        [
          'INVALID_IMAGE',
          'IMAGE_TOO_LARGE',
          'IMAGE_DECODE_FAILED',
          'MODEL_INFERENCE_FAILED',
          'INTERNAL_ERROR'
        ] as GrowthDetectErrorCode[]
      ).find((code) => rawMessage.includes(code))

      errorCode.value = matchedCode ?? 'INTERNAL_ERROR'
      errorMessage.value = mapImageErrorMessage(errorCode.value)
      ElMessage.error(errorMessage.value)
    }
  }

  const handleVideoUpload = async (file: File) => {
    resetImageState()
    inputMode.value = 'growthVideo'

    try {
      await uploadVideo(file)
      ElMessage.success('视频已上传，正在识别关键帧')
    } catch (error: any) {
      const rawMessage = String(error?.message || '')
      const matchedCode = (
        [
          'INVALID_VIDEO',
          'VIDEO_TOO_LARGE',
          'VIDEO_DECODE_FAILED',
          'NO_VALID_FRAMES',
          'MODEL_INFERENCE_FAILED',
          'INTERNAL_ERROR'
        ] as GrowthVideoDetectErrorCode[]
      ).find((code) => rawMessage.includes(code))

      markVideoTaskFailed(matchedCode ?? 'INTERNAL_ERROR')
      ElMessage.error(mapVideoErrorMessage(matchedCode ?? 'INTERNAL_ERROR'))
    }
  }

  const handleSelectDetection = (id: string) => {
    if (inputMode.value === 'growthVideo') {
      selectFrameDetection(id)
      return
    }

    selectedDetectionId.value = id
  }

  const handleSelectFrame = (frameId: string) => {
    selectGrowthFrame(frameId)
  }

  const handleClear = () => {
    resetAllState()
    ElMessage.info('已清空识别结果')
  }

  watch(isProcessing, (value) => {
    if (value) {
      loadingService.showLoading()
      return
    }

    loadingService.hideLoading()
  })

  watch(growthVideoTaskStatus, (value, previous) => {
    if (!previous || previous === value) return

    if (value === 'success') {
      ElMessage.success('视频关键帧识别完成')
    }

    if (value === 'failed') {
      ElMessage.error(activeErrorMessage.value || '视频识别失败，请稍后重试')
    }
  })

  onUnmounted(() => {
    loadingService.hideLoading()
  })
</script>

<style scoped lang="scss">
  .growth-monitoring-detect {
    padding: 20px;

    .page-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 16px 20px;
      margin-bottom: 20px;
      background: var(--el-bg-color);
      border-radius: 8px;
      box-shadow: 0 2px 12px 0 rgb(0 0 0 / 10%);

      .title-section {
        display: flex;
        gap: 12px;
        align-items: center;

        h2 {
          margin: 0;
          font-size: 24px;
          font-weight: 600;
          background: linear-gradient(135deg, #1890ff 0%, #36cfc9 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }
      }
    }

    .mb-4 {
      margin-bottom: 16px;
    }
  }
</style>
