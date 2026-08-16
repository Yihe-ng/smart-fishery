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

    <el-row
      :gutter="20"
      class="growth-workspace-row"
      :class="{
        'is-image-mode': inputMode !== 'growthVideo',
        'is-video-mode': inputMode === 'growthVideo'
      }"
    >
      <el-col :xs="24" :sm="24" :md="8" :lg="6" class="growth-sidebar-col">
        <div
          class="growth-sidebar-stack"
          :class="{
            'is-image-mode': inputMode !== 'growthVideo',
            'is-video-mode': inputMode === 'growthVideo'
          }"
          :style="sidebarStackStyle"
        >
          <GrowthStatsSummary
            :stats="activeStats"
            :assessment="activeAssessment"
            :summary="activeSummary"
            :culture-month="cultureMonth"
            :video-mode="inputMode === 'growthVideo'"
            :evaluating="isReevaluating"
          />
          <div v-if="showFeedingEntry" class="feeding-entry-tip">
            <span>识别完成，可查看联动投喂建议</span>
            <ElButton type="primary" text size="small" @click="goToFeeding">
              前往精准投喂
              <ArtSvgIcon icon="ri:arrow-right-line" />
            </ElButton>
          </div>
          <GrowthResultCard :result="activeDetection" :empty-text="resultEmptyText" />
        </div>
      </el-col>

      <el-col :xs="24" :sm="24" :md="16" :lg="18" class="growth-main-col">
        <div ref="mainStackRef" class="growth-main-stack">
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
            :stage="growthVideoStage"
            :progress="growthVideoProgress"
            :filename="growthVideoMeta?.filename"
            :frame-count="growthVideoFrames.length"
            :planned-frame-count="growthVideoPlannedFrameCount"
            :completed-frame-count="growthVideoCompletedFrameCount"
            :evaluable-frame-count="growthVideoEvaluableFrameCount"
            :detection-occurrence-count="growthVideoDetectionOccurrenceCount"
            :aggregate-stats="growthVideoAggregateStats"
            :is-partial="growthVideoIsPartial"
            :is-cancelling="growthVideoIsCancelling"
            :error-message="activeErrorMessage"
            @cancel="handleCancelVideo"
          />

          <GrowthVideoFrameStrip
            v-if="inputMode === 'growthVideo' && growthVideoFrames.length"
            :frames="growthVideoFrames"
            :selected-frame-id="selectedGrowthFrameId"
            @select="handleSelectFrame"
          />

          <GrowthAssessmentControls
            ref="assessmentControlsRef"
            v-model:culture-month="cultureMonth"
            v-model:stocking-avg-length-cm="stockingAvgLengthCm"
            :reference-preview="referencePreview"
            :errors="assessmentErrors"
            :disabled="isProcessing"
            @commit-length="handleStockingLengthCommit"
            @clear-errors="clearAssessmentErrors"
          />

          <GrowthActionButtons
            :processing="isProcessing"
            :has-image="hasVisualResult"
            :before-image-upload="validateAssessmentParamsBeforeUpload"
            @upload-image="handleImageUpload"
            @upload-video="handleVideoUpload"
            @clear="handleClear"
          />
        </div>
      </el-col>
    </el-row>

    <!-- 三阶段处理流程动画：随请求开始/结束显示隐藏，纯前端动画，不代表真实进度 -->
    <GrowthProcessAnimation
      v-if="isProcessing"
      :is-video="inputMode === 'growthVideo'"
      :stage="growthVideoStage"
      :completed-frame-count="growthVideoCompletedFrameCount"
      :planned-frame-count="growthVideoPlannedFrameCount"
      :cancelling="growthVideoIsCancelling"
      :show-cancel="['queued', 'processing'].includes(growthVideoTaskStatus ?? '')"
      @cancel="handleCancelVideo"
    />
  </div>
</template>

<script setup lang="ts">
  import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
  import { useRouter } from 'vue-router'
  import { ElMessage, ElMessageBox } from 'element-plus'
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import { detectGrowth, evaluateGrowth, evaluateGrowthVideo } from '@/api/growth-monitoring/detect'
  import {
    DEFAULT_GROWTH_POND_ID,
    useGrowthRecognitionStore
  } from '@/store/modules/growth-recognition'
  import { loadingService } from '@/utils/ui'
  import type {
    GrowthAssessment,
    GrowthDetectErrorCode,
    GrowthDetectResponse,
    GrowthDetectionItem,
    GrowthImageMeta,
    GrowthStats,
    GrowthSummary,
    GrowthTaskStatus,
    GrowthVideoDetectErrorCode
  } from '@/types/growth-monitoring'
  import {
    UNKNOWN_CULTURE_MONTH,
    formatLengthCm,
    isKnownCultureMonth,
    isValidStockingLength,
    type CultureMonthSelection,
    type GrowthAssessmentErrors
  } from './constants/assessmentParams'
  import GrowthActionButtons from './components/GrowthActionButtons.vue'
  import GrowthAssessmentControls from './components/GrowthAssessmentControls.vue'
  import GrowthImageDisplay from './components/GrowthImageDisplay.vue'
  import GrowthProcessAnimation from './components/GrowthProcessAnimation.vue'
  import GrowthResultCard from './components/GrowthResultCard.vue'
  import GrowthStatsSummary from './components/GrowthStatsSummary.vue'
  import GrowthVideoFrameStrip from './components/GrowthVideoFrameStrip.vue'
  import GrowthVideoTaskState from './components/GrowthVideoTaskState.vue'
  import { useGrowthVideoTask } from './composables/useGrowthVideoTask'
  import { useGrowthRecordSync } from './composables/useGrowthRecordSync'

  defineOptions({ name: 'GrowthMonitoringDetect' })

  type InputMode = 'image' | 'growthVideo'

  const EMPTY_STATS: GrowthStats = {
    small: 0,
    normal: 0,
    large: 0,
    unassessed: 0,
    detectedCount: 0,
    measurableCount: 0,
    unmeasurableCount: 0
  }

  const EMPTY_SUMMARY: GrowthSummary = {
    avgBodyLengthCm: 0,
    avgWeightG: 0
  }

  const inputMode = ref<InputMode>('image')
  const taskStatus = ref<GrowthTaskStatus>('idle')
  const imageMeta = ref<GrowthImageMeta | null>(null)
  const detections = ref<GrowthDetectionItem[]>([])
  const selectedDetectionId = ref<string | null>(null)
  const stats = ref<GrowthStats>({ ...EMPTY_STATS })
  const summary = ref<GrowthSummary>({ ...EMPTY_SUMMARY })
  const assessment = ref<GrowthAssessment | null>(null)
  const errorCode = ref<GrowthDetectErrorCode | null>(null)
  const errorMessage = ref('')
  const mainStackRef = ref<HTMLElement>()
  const mainStackHeight = ref(0)
  let mainStackResizeObserver: ResizeObserver | null = null

  const {
    growthVideoTaskStatus,
    growthVideoStage,
    growthVideoTaskId,
    growthVideoFrames,
    selectedGrowthFrameId,
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
    selectFrameDetection
  } = useGrowthVideoTask()

  const growthRecognitionStore = useGrowthRecognitionStore()
  const { syncRecord, syncReevaluated } = useGrowthRecordSync()
  const router = useRouter()

  // 首次使用没有记忆值时保持为空，不自动填入 13 cm（方案 §5.2）。
  const cultureMonth = ref<CultureMonthSelection>(
    growthRecognitionStore.recentParams.cultureMonth ?? null
  )
  const stockingAvgLengthCm = ref<number | null>(
    growthRecognitionStore.recentParams.stockingAvgLengthCm ?? null
  )
  const assessmentErrors = ref<GrowthAssessmentErrors>({})
  const assessmentControlsRef = ref<{ focusFirstError: () => void; flashErrors: () => void }>()
  const isReevaluating = ref(false)
  // 重评请求序号：只接受序号最新的响应，避免连续改参数时旧响应覆盖新结论。
  let reevaluateRequestSeq = 0
  let reevaluateAbortController: AbortController | null = null
  let restoringAssessmentParams = false
  let lastSuccessfulAssessmentParams = {
    cultureMonth: cultureMonth.value,
    stockingAvgLengthCm: stockingAvgLengthCm.value
  }

  const imageSelectedDetection = computed(
    () => detections.value.find((item) => item.id === selectedDetectionId.value) ?? null
  )

  const activeImage = computed(() =>
    inputMode.value === 'growthVideo' ? (selectedGrowthFrame.value?.image ?? null) : imageMeta.value
  )

  const activeDetections = computed(() =>
    inputMode.value === 'growthVideo'
      ? (selectedGrowthFrame.value?.detections ?? [])
      : detections.value
  )

  const activeSelectedDetectionId = computed(() =>
    inputMode.value === 'growthVideo'
      ? (selectedGrowthFrame.value?.selectedDetectionId ?? null)
      : selectedDetectionId.value
  )

  const activeDetection = computed(() =>
    inputMode.value === 'growthVideo'
      ? (selectedGrowthFrame.value?.detections.find(
          (item) => item.id === selectedGrowthFrame.value?.selectedDetectionId
        ) ?? null)
      : imageSelectedDetection.value
  )

  const activeStats = computed(() =>
    inputMode.value === 'growthVideo' ? growthVideoAggregateStats.value : stats.value
  )

  const activeSummary = computed(() =>
    inputMode.value === 'growthVideo' ? growthVideoAggregateSummary.value : summary.value
  )

  const activeAssessment = computed(() =>
    inputMode.value === 'growthVideo' ? growthVideoAssessment.value : assessment.value
  )

  const showFeedingEntry = computed(() => {
    if (inputMode.value === 'image') {
      return taskStatus.value === 'success' && detections.value.length > 0
    }
    return (
      growthVideoTaskStatus.value === 'success' &&
      growthVideoAssessment.value?.sampleSufficient === true &&
      growthVideoAssessment.value.cohortStatus !== 'unassessed' &&
      growthVideoAssessment.value.cohortStatus !== 'insufficient'
    )
  })

  const goToFeeding = () => router.push({ name: 'Feeding' })

  /**
   * 上传前的参考范围预览：仅在月份与投苗体长均有效时展示。
   * 参考全长与上下限来自最近一次后端评价结果，前端不复制计算公式；
   * 尚无后端结果时只展示已选月份，不猜测参考范围。
   */
  const referencePreview = computed(() => {
    if (!isKnownCultureMonth(cultureMonth.value)) return ''
    if (!isValidStockingLength(stockingAvgLengthCm.value)) return ''

    const monthText = `投苗后第 ${cultureMonth.value} 个月`
    const evaluated = activeAssessment.value

    if (
      !evaluated ||
      evaluated.cultureMonth !== cultureMonth.value ||
      evaluated.stockingAvgLengthCm !== stockingAvgLengthCm.value ||
      evaluated.referenceLengthCm === null ||
      evaluated.smallThresholdCm === null ||
      evaluated.largeThresholdCm === null
    ) {
      return `${monthText}｜投苗时平均全长 ${formatLengthCm(stockingAvgLengthCm.value)} cm`
    }

    return `${monthText}｜综合参考全长 ${formatLengthCm(evaluated.referenceLengthCm)} cm｜正常参考范围 ${formatLengthCm(evaluated.smallThresholdCm)}–${formatLengthCm(evaluated.largeThresholdCm)} cm`
  })

  const displayTaskStatus = computed<GrowthTaskStatus>(() => {
    if (inputMode.value === 'growthVideo') {
      if (
        growthVideoTaskStatus.value === 'queued' ||
        growthVideoTaskStatus.value === 'processing'
      ) {
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

  const sidebarStackStyle = computed(() => {
    if (inputMode.value !== 'growthVideo' || mainStackHeight.value <= 0) return undefined

    return {
      '--growth-sidebar-height': `${mainStackHeight.value}px`
    }
  })

  const activeErrorMessage = computed(() => {
    if (inputMode.value === 'growthVideo') {
      return mapVideoErrorMessage(growthVideoErrorCode.value)
    }
    return errorMessage.value
  })

  const resultEmptyText = computed(() => {
    if (
      displayTaskStatus.value === 'success' &&
      activeImage.value &&
      !activeDetections.value.length
    ) {
      return inputMode.value === 'growthVideo' ? '当前关键帧未识别到石斑鱼' : '未识别到石斑鱼'
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
    summary.value = { ...EMPTY_SUMMARY }
    assessment.value = null
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
      case 'GROWTH_INFERENCE_BUSY':
        return '当前已有生长识别任务正在处理，请稍后重试。'
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
      case 'VIDEO_TOO_SHORT':
        return '视频时长过短，请上传至少 3 秒的视频。'
      case 'NO_VALID_FRAMES':
        return '未提取到有效关键帧，请尝试更清晰的视频。'
      case 'PROCESS_TIMEOUT':
        return '视频处理达到时间限制，已保留已完成关键帧。'
      case 'PARTIAL_FRAME_FAILURE':
        return '部分关键帧处理失败，已保留其他结果。'
      case 'GROWTH_INFERENCE_BUSY':
        return '当前已有生长识别任务正在处理，请稍后重试。'
      case 'MODEL_INFERENCE_FAILED':
        return '模型推理失败，请稍后重试。'
      case 'INTERNAL_ERROR':
        return '系统异常，请稍后重试。'
      case 'USER_CANCELLED':
        return '本次视频识别已取消。'
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
    summary.value = response.summary
    // 评价失败时后端返回 assessment=null，但体长测量结果仍然有效，必须保留。
    assessment.value = response.assessment ?? null
    errorCode.value = response.errorCode
    errorMessage.value = mapImageErrorMessage(response.errorCode)
  }

  const getAverageConfidence = (items: GrowthDetectionItem[]) => {
    const validConfidences = items
      .map((item) => item.confidence)
      .filter((value) => Number.isFinite(value))

    if (!validConfidences.length) return undefined

    const total = validConfidences.reduce((sum, value) => sum + value, 0)
    return Number((total / validConfidences.length).toFixed(3))
  }

  const writeImageRecognitionSummary = (response: GrowthDetectResponse) => {
    if (
      response.taskStatus !== 'success' ||
      response.errorCode ||
      response.stats.detectedCount <= 0
    ) {
      return
    }

    // 第一阶段生长识别页没有池塘选择，先写入默认池塘，避免跨页摘要缺少业务归属。
    const pondId = DEFAULT_GROWTH_POND_ID
    const evaluated = response.assessment ?? null

    growthRecognitionStore.setLatestSummary({
      pondId,
      sourceType: 'image',
      sampleSource: 'user-upload',
      detectedCount: response.stats.detectedCount,
      measurableCount: response.stats.measurableCount,
      unmeasurableCount: response.stats.unmeasurableCount,
      small: response.stats.small,
      normal: response.stats.normal,
      large: response.stats.large,
      avgBodyLengthCm: response.summary.avgBodyLengthCm,
      avgWeightG: response.summary.avgWeightG,
      avgConfidence: getAverageConfidence(response.detections),
      isDemoData: false,
      cultureMonth: evaluated?.cultureMonth ?? null,
      stockingAvgLengthCm: evaluated?.stockingAvgLengthCm ?? null,
      referenceLengthCm: evaluated?.referenceLengthCm ?? null,
      smallThresholdCm: evaluated?.smallThresholdCm ?? null,
      largeThresholdCm: evaluated?.largeThresholdCm ?? null,
      trimmedMeanLengthCm: evaluated?.trimmedMeanLengthCm ?? null,
      allMeasurableAvgLengthCm: evaluated?.allMeasurableAvgLengthCm ?? null,
      cohortStatus: evaluated?.cohortStatus ?? 'unassessed',
      advice: evaluated?.advice ?? null,
      perStatus: {
        small: response.stats.small,
        normal: response.stats.normal,
        large: response.stats.large,
        unassessed: response.stats.unassessed
      }
    })

    const saved = growthRecognitionStore.getLatestSummary(pondId)
    if (saved) syncRecord(saved)
  }

  const writeVideoRecognitionSummary = () => {
    if (
      growthVideoTaskStatus.value !== 'success' ||
      growthVideoAggregateStats.value.detectedCount <= 0
    ) {
      return
    }

    // 第一阶段生长识别页没有池塘选择，先写入默认池塘，避免跨页摘要缺少业务归属。
    const pondId = DEFAULT_GROWTH_POND_ID
    const evaluated = growthVideoAssessment.value

    growthRecognitionStore.setLatestSummary({
      pondId,
      sourceType: 'video',
      sampleSource: 'video-task',
      taskId: growthVideoTaskId.value ?? undefined,
      detectedCount: growthVideoAggregateStats.value.detectedCount,
      measurableCount: growthVideoAggregateStats.value.measurableCount,
      unmeasurableCount: growthVideoAggregateStats.value.unmeasurableCount,
      plannedFrameCount: growthVideoPlannedFrameCount.value,
      completedFrameCount: growthVideoCompletedFrameCount.value,
      evaluableFrameCount: growthVideoEvaluableFrameCount.value,
      detectionOccurrenceCount: growthVideoDetectionOccurrenceCount.value,
      measurableOccurrenceCount: growthVideoMeasurableOccurrenceCount.value,
      small: 0,
      normal: 0,
      large: 0,
      avgBodyLengthCm: growthVideoAggregateSummary.value.avgBodyLengthCm,
      avgWeightG: growthVideoAggregateSummary.value.avgWeightG,
      avgConfidence: undefined,
      isDemoData: false,
      cultureMonth: evaluated?.cultureMonth ?? null,
      stockingAvgLengthCm: evaluated?.stockingAvgLengthCm ?? null,
      referenceLengthCm: evaluated?.referenceLengthCm ?? null,
      smallThresholdCm: evaluated?.smallThresholdCm ?? null,
      largeThresholdCm: evaluated?.largeThresholdCm ?? null,
      trimmedMeanLengthCm: evaluated?.trimmedMeanLengthCm ?? null,
      allMeasurableAvgLengthCm: evaluated?.allMeasurableAvgLengthCm ?? null,
      cohortStatus: evaluated?.cohortStatus ?? 'unassessed',
      advice: evaluated?.advice ?? null,
      perStatus: {
        small: 0,
        normal: 0,
        large: 0,
        unassessed: 0
      }
    })

    const saved = growthRecognitionStore.getLatestSummary(pondId)
    if (saved) syncRecord(saved)
  }

  const clearAssessmentErrors = () => {
    if (!assessmentErrors.value.cultureMonth && !assessmentErrors.value.stockingAvgLengthCm) return
    assessmentErrors.value = {}
  }

  /**
   * 上传前校验养殖参数，负责在打开文件选择器之前拦截无效输入。
   * 月份必须已选择；选择“不清楚，仅测量体长”时豁免投苗体长校验，可直接上传。
   * 校验失败会写入中文错误文案，由参数区高亮闪烁并聚焦第一个错误字段；返回 false 阻止弹出文件选择窗口。
   * 校验通过时把本次参数写入 store 记忆（长期保留，不随清空结果失效）。
   */
  const validateAssessmentParamsBeforeUpload = () => {
    const errors: GrowthAssessmentErrors = {}
    const isUnknownMonth = cultureMonth.value === UNKNOWN_CULTURE_MONTH

    if (cultureMonth.value === null) {
      errors.cultureMonth = '请选择养殖月数；若确实不清楚，请选择“不清楚，仅测量体长”'
    } else if (!isUnknownMonth && !isKnownCultureMonth(cultureMonth.value)) {
      errors.cultureMonth = '养殖月数需在第 3–15 个月之间'
    }

    if (!isUnknownMonth && cultureMonth.value !== null) {
      if (stockingAvgLengthCm.value === null) {
        errors.stockingAvgLengthCm = '请填写投苗时平均全长（cm）'
      } else if (!isValidStockingLength(stockingAvgLengthCm.value)) {
        errors.stockingAvgLengthCm = '投苗时平均全长需在 1.0–100.0 cm 之间'
      }
    }

    assessmentErrors.value = errors

    if (errors.cultureMonth || errors.stockingAvgLengthCm) {
      assessmentControlsRef.value?.flashErrors()
      assessmentControlsRef.value?.focusFirstError()
      return false
    }

    growthRecognitionStore.setRecentParams({
      cultureMonth: isUnknownMonth ? undefined : cultureMonth.value,
      stockingAvgLengthCm: isUnknownMonth ? undefined : stockingAvgLengthCm.value
    })

    return true
  }

  /** 传给后端的评价参数：选择“不清楚”时两个字段都置空，后端只测量体长 */
  const buildAssessmentParams = () => {
    if (!isKnownCultureMonth(cultureMonth.value)) {
      return { cultureMonth: null, stockingAvgLengthCm: null }
    }

    return {
      cultureMonth: cultureMonth.value,
      stockingAvgLengthCm: isValidStockingLength(stockingAvgLengthCm.value)
        ? stockingAvgLengthCm.value
        : null
    }
  }

  /** 只用于刷新恢复页面输入；后端参数始终使用 buildAssessmentParams 的空值语义。 */
  const buildVideoTaskSnapshot = () => ({
    cultureMonth: cultureMonth.value,
    stockingAvgLengthCm: isValidStockingLength(stockingAvgLengthCm.value)
      ? stockingAvgLengthCm.value
      : null
  })

  const rememberSuccessfulAssessmentParams = () => {
    lastSuccessfulAssessmentParams = {
      cultureMonth: cultureMonth.value,
      stockingAvgLengthCm: stockingAvgLengthCm.value
    }
    growthRecognitionStore.setRecentParams(lastSuccessfulAssessmentParams)
  }

  const invalidateReevaluation = () => {
    reevaluateAbortController?.abort()
    reevaluateAbortController = null
    reevaluateRequestSeq += 1
    isReevaluating.value = false
  }

  const handleImageUpload = async (imgData: string) => {
    invalidateReevaluation()
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
    summary.value = { ...EMPTY_SUMMARY }
    assessment.value = null
    errorCode.value = null
    errorMessage.value = ''

    try {
      taskStatus.value = 'processing'
      const result = await detectGrowth(imgData, buildAssessmentParams())
      applyDetectResponse(result)
      writeImageRecognitionSummary(result)
      rememberSuccessfulAssessmentParams()

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
      summary.value = { ...EMPTY_SUMMARY }
      assessment.value = null

      const rawMessage = String(error?.message || '')
      const matchedCode = (
        [
          'INVALID_IMAGE',
          'IMAGE_TOO_LARGE',
          'IMAGE_DECODE_FAILED',
          'GROWTH_INFERENCE_BUSY',
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
    invalidateReevaluation()
    resetImageState()
    inputMode.value = 'growthVideo'

    try {
      await uploadVideo(file, buildAssessmentParams(), buildVideoTaskSnapshot())
      ElMessage.success('视频已上传，正在识别关键帧')
    } catch (error: any) {
      const rawMessage = String(error?.message || '')
      const matchedCode = (
        [
          'INVALID_VIDEO',
          'VIDEO_TOO_LARGE',
          'VIDEO_DECODE_FAILED',
          'VIDEO_TOO_SHORT',
          'NO_VALID_FRAMES',
          'PROCESS_TIMEOUT',
          'PARTIAL_FRAME_FAILURE',
          'GROWTH_INFERENCE_BUSY',
          'MODEL_INFERENCE_FAILED',
          'INTERNAL_ERROR'
        ] as GrowthVideoDetectErrorCode[]
      ).find((code) => rawMessage.includes(code))

      markVideoTaskFailed(matchedCode ?? 'INTERNAL_ERROR')
      ElMessage.error(mapVideoErrorMessage(matchedCode ?? 'INTERNAL_ERROR'))
    }
  }

  const handleCancelVideo = async () => {
    try {
      await ElMessageBox.confirm(
        '确认取消当前视频识别吗？当前正在处理的关键帧会完成，已完成结果会保留。',
        '取消视频识别',
        { type: 'warning', confirmButtonText: '确认取消', cancelButtonText: '继续识别' }
      )
    } catch {
      return
    }

    try {
      await cancelVideoTask()
    } catch {
      ElMessage.warning('取消请求未完成，请稍后重试')
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

  // 只清图片与识别结果；已记忆的养殖参数按方案 §5.2 保留，方便连续识别同一批鱼。
  const handleClear = () => {
    invalidateReevaluation()
    if (
      growthVideoTaskId.value &&
      ['success', 'failed', 'cancelled'].includes(growthVideoTaskStatus.value ?? '')
    ) {
      void releaseVideoTask().catch(() => undefined)
    } else {
      resetAllState()
    }
    ElMessage.info('已清空识别结果')
  }

  /**
   * 识别完成后修改养殖参数时的轻量重评。
   * 月份修改立即触发，投苗体长修改在失焦或回车时触发，避免每敲一位数字都发请求。
   * 只把已有的单鱼可测性与体长发给后端重算状态，不重新上传图片、不重新运行模型。
   * 连续修改时先 abort 旧请求，并用请求序号丢弃迟到的旧响应，防止乱序覆盖最新结论。
   * 重评失败保留上一次成功的结论与参数，也不覆盖 store 里的成功摘要。
   */
  const reevaluateAssessment = async () => {
    if (inputMode.value === 'growthVideo') {
      if (growthVideoTaskStatus.value !== 'success' || !growthVideoFrames.value.length) return

      const params = buildAssessmentParams()
      if (isKnownCultureMonth(cultureMonth.value) && params.stockingAvgLengthCm === null) return

      reevaluateAbortController?.abort()
      const controller = new AbortController()
      reevaluateAbortController = controller
      const requestSeq = ++reevaluateRequestSeq
      isReevaluating.value = true

      try {
        const response = await evaluateGrowthVideo(
          {
            cultureMonth: params.cultureMonth,
            stockingAvgLengthCm: params.stockingAvgLengthCm,
            frames: growthVideoFrames.value.map((frame) => ({
              frameId: frame.frameId,
              fishMeasurements: frame.detections.map((item) => ({
                id: item.id,
                isMeasurable: item.isMeasurable,
                bodyLengthCm: item.bodyLengthCm
              }))
            }))
          },
          { signal: controller.signal }
        )
        if (requestSeq !== reevaluateRequestSeq) return

        const resultByFrameId = new Map(response.frames.map((item) => [item.frameId, item]))
        const nextFrames = growthVideoFrames.value.map((frame) => {
          const evaluated = resultByFrameId.get(frame.frameId)
          if (!evaluated) return frame
          const statusById = new Map(evaluated.detections.map((item) => [item.id, item]))
          return {
            ...frame,
            detections: frame.detections.map((item) => {
              const status = statusById.get(item.id)
              return status
                ? { ...item, status: status.status, statusText: status.statusText }
                : item
            }),
            stats: evaluated.stats,
            summary: evaluated.summary,
            assessment: evaluated.assessment,
            frameStatus: evaluated.frameStatus
          }
        })
        growthVideoFrames.value = nextFrames
        growthVideoAggregateStats.value = nextFrames.reduce<GrowthStats>(
          (total, frame) => ({
            small: total.small + frame.stats.small,
            normal: total.normal + frame.stats.normal,
            large: total.large + frame.stats.large,
            unassessed: total.unassessed + frame.stats.unassessed,
            detectedCount: total.detectedCount + frame.stats.detectedCount,
            measurableCount: total.measurableCount + frame.stats.measurableCount,
            unmeasurableCount: total.unmeasurableCount + frame.stats.unmeasurableCount
          }),
          { ...EMPTY_STATS }
        )
        growthVideoEvaluableFrameCount.value = nextFrames.filter(
          (frame) => frame.frameStatus === 'evaluable'
        ).length
        growthVideoAssessment.value = response.assessment
        growthVideoAggregateSummary.value = response.summary
        rememberSuccessfulAssessmentParams()
        writeVideoRecognitionSummary()
      } catch {
        if (requestSeq === reevaluateRequestSeq) {
          restoringAssessmentParams = true
          cultureMonth.value = lastSuccessfulAssessmentParams.cultureMonth
          stockingAvgLengthCm.value = lastSuccessfulAssessmentParams.stockingAvgLengthCm
          await nextTick()
          restoringAssessmentParams = false
          ElMessage.warning('生长评价更新失败，仍展示上一次评价结果')
        }
      } finally {
        if (requestSeq === reevaluateRequestSeq) {
          isReevaluating.value = false
          reevaluateAbortController = null
        }
      }
      return
    }

    if (taskStatus.value !== 'success' || !detections.value.length) return

    const params = buildAssessmentParams()
    if (isKnownCultureMonth(cultureMonth.value) && params.stockingAvgLengthCm === null) return

    reevaluateAbortController?.abort()
    const controller = new AbortController()
    reevaluateAbortController = controller
    const requestSeq = ++reevaluateRequestSeq
    isReevaluating.value = true

    try {
      const response = await evaluateGrowth(
        {
          cultureMonth: params.cultureMonth,
          stockingAvgLengthCm: params.stockingAvgLengthCm,
          fishMeasurements: detections.value.map((item) => ({
            id: item.id,
            isMeasurable: item.isMeasurable,
            bodyLengthCm: item.bodyLengthCm
          }))
        },
        { signal: controller.signal }
      )

      if (requestSeq !== reevaluateRequestSeq) return

      const statusById = new Map(response.detections.map((item) => [item.id, item]))
      detections.value = detections.value.map((item) => {
        const evaluated = statusById.get(item.id)
        return evaluated
          ? { ...item, status: evaluated.status, statusText: evaluated.statusText }
          : item
      })
      stats.value = response.stats
      summary.value = response.summary
      assessment.value = response.assessment

      writeReevaluatedSummary(response.assessment, response.stats)
      rememberSuccessfulAssessmentParams()
    } catch {
      if (requestSeq === reevaluateRequestSeq) {
        restoringAssessmentParams = true
        cultureMonth.value = lastSuccessfulAssessmentParams.cultureMonth
        stockingAvgLengthCm.value = lastSuccessfulAssessmentParams.stockingAvgLengthCm
        await nextTick()
        restoringAssessmentParams = false
        ElMessage.warning('生长评价更新失败，仍展示上一次评价结果')
      }
    } finally {
      if (requestSeq === reevaluateRequestSeq) {
        isReevaluating.value = false
        reevaluateAbortController = null
      }
    }
  }

  /** 重评成功后覆盖摘要中的评价字段，保持 24 小时有效期的起点仍是首次识别时间 */
  const writeReevaluatedSummary = (evaluated: GrowthAssessment | null, nextStats: GrowthStats) => {
    const existing = growthRecognitionStore.getLatestSummary(DEFAULT_GROWTH_POND_ID)
    if (!existing) return

    growthRecognitionStore.setLatestSummary({
      ...existing,
      small: nextStats.small,
      normal: nextStats.normal,
      large: nextStats.large,
      cultureMonth: evaluated?.cultureMonth ?? null,
      stockingAvgLengthCm: evaluated?.stockingAvgLengthCm ?? null,
      referenceLengthCm: evaluated?.referenceLengthCm ?? null,
      smallThresholdCm: evaluated?.smallThresholdCm ?? null,
      largeThresholdCm: evaluated?.largeThresholdCm ?? null,
      trimmedMeanLengthCm: evaluated?.trimmedMeanLengthCm ?? null,
      allMeasurableAvgLengthCm: evaluated?.allMeasurableAvgLengthCm ?? null,
      cohortStatus: evaluated?.cohortStatus ?? 'unassessed',
      advice: evaluated?.advice ?? null,
      perStatus: {
        small: nextStats.small,
        normal: nextStats.normal,
        large: nextStats.large,
        unassessed: nextStats.unassessed
      }
    })

    const updated = growthRecognitionStore.getLatestSummary(DEFAULT_GROWTH_POND_ID)
    if (updated) syncReevaluated(updated)
  }

  /** 投苗体长失焦或回车时提交；仅在重评成功后记忆新参数。 */
  const handleStockingLengthCommit = () => {
    reevaluateAssessment()
  }

  // 月份变更立即重评；选择“不清楚”时同样触发，让状态回落为“未评估”。
  watch(cultureMonth, () => {
    if (restoringAssessmentParams) return
    reevaluateAssessment()
  })

  watch(restoredAssessmentParams, (params) => {
    if (!params) return
    inputMode.value = 'growthVideo'
    restoringAssessmentParams = true
    cultureMonth.value = params.cultureMonth as CultureMonthSelection
    stockingAvgLengthCm.value = params.stockingAvgLengthCm ?? null
    nextTick(() => {
      restoringAssessmentParams = false
    })
  })

  watch(isProcessing, (value) => {
    if (value) {
      loadingService.showLoading()
      return
    }

    loadingService.hideLoading()
  })

  watch(growthVideoTaskStatus, (value, previous) => {
    if (previous === value) return

    if (value === 'success') {
      writeVideoRecognitionSummary()
      ElMessage.success(
        growthVideoIsPartial.value ? '视频部分关键帧识别完成' : '视频关键帧识别完成'
      )
    }

    if (value === 'cancelled') ElMessage.info('视频识别已取消，已完成关键帧仍可查看')

    if (value === 'failed') {
      ElMessage.error(activeErrorMessage.value || '视频识别失败，请稍后重试')
    }
  })

  const syncMainStackHeight = () => {
    const target = mainStackRef.value
    if (!target) return

    mainStackHeight.value = target.getBoundingClientRect().height
  }

  onMounted(async () => {
    await nextTick()
    syncMainStackHeight()

    if (mainStackRef.value) {
      mainStackResizeObserver = new ResizeObserver(syncMainStackHeight)
      mainStackResizeObserver.observe(mainStackRef.value)
    }
  })

  onUnmounted(() => {
    mainStackResizeObserver?.disconnect()
    reevaluateAbortController?.abort()
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

    .growth-workspace-row {
      align-items: stretch;
    }

    .growth-sidebar-col,
    .growth-main-col {
      display: flex;
      flex-direction: column;
      min-height: 0;
    }

    .growth-sidebar-stack {
      display: flex;
      flex: 1;
      flex-direction: column;
      min-height: 0;
    }

    .feeding-entry-tip {
      display: flex;
      gap: 8px;
      align-items: center;
      justify-content: space-between;
      padding: 8px 12px;
      margin-top: 10px;
      font-size: 12px;
      color: var(--el-text-color-secondary);
      background: var(--el-color-primary-light-9);
      border: 1px solid var(--el-color-primary-light-7);
      border-radius: 8px;
    }

    .growth-main-stack {
      display: flex;
      flex: 1;
      flex-direction: column;
      min-height: 0;
    }

    @media (width <= 768px) {
      .growth-workspace-row {
        height: auto;
        min-height: 0;
      }

      .growth-sidebar-col {
        margin-bottom: 16px;
      }
    }

    @media (width > 768px) {
      .growth-sidebar-stack.is-video-mode {
        height: var(--growth-sidebar-height);
        max-height: var(--growth-sidebar-height);
      }

      .growth-sidebar-stack.is-image-mode {
        flex: initial;
      }
    }
  }
</style>
