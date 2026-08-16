export type GrowthTaskStatus = 'idle' | 'uploading' | 'processing' | 'success' | 'failed'
export type GrowthVideoTaskStatus = 'queued' | 'processing' | 'success' | 'failed' | 'cancelled'
export type GrowthVideoTaskStage = 'queued' | 'preparing' | 'analyzing' | 'finalizing'
export type GrowthVideoFrameStatus = 'evaluable' | 'insufficient_sample' | 'no_valid_detection'

/**
 * 单鱼生长状态。
 * - small / normal / large：已按当月综合参考全长完成月度分档
 * - unassessed：鱼体可测长，但未提供养殖月数（或评价配置不可用），因此不做月度分档
 * - unmeasurable：鱼体无法可靠测长，不参与任何平均值与分档
 */
export type GrowthStatus = 'small' | 'normal' | 'large' | 'unassessed' | 'unmeasurable'

/**
 * 群体生长状态。
 * insufficient = 有效可测样本不足（少于配置的最小可测数量），不产生群体分档结论。
 * unassessed = 未提供养殖月数，仅完成体长测量。
 */
export type GrowthCohortStatus = 'small' | 'normal' | 'large' | 'insufficient' | 'unassessed'

export type GrowthDetectErrorCode =
  | 'INVALID_IMAGE'
  | 'IMAGE_TOO_LARGE'
  | 'IMAGE_DECODE_FAILED'
  | 'GROWTH_INFERENCE_BUSY'
  | 'NO_FISH_DETECTED'
  | 'MODEL_INFERENCE_FAILED'
  | 'INTERNAL_ERROR'

export type GrowthVideoDetectErrorCode =
  | 'INVALID_VIDEO'
  | 'VIDEO_TOO_LARGE'
  | 'VIDEO_DECODE_FAILED'
  | 'VIDEO_TOO_SHORT'
  | 'NO_VALID_FRAMES'
  | 'PROCESS_TIMEOUT'
  | 'PARTIAL_FRAME_FAILURE'
  | 'USER_CANCELLED'
  | 'GROWTH_INFERENCE_BUSY'
  | 'MODEL_INFERENCE_FAILED'
  | 'INTERNAL_ERROR'

export interface GrowthAssessmentParams {
  cultureMonth?: number | null
  stockingAvgLengthCm?: number | null
}

export interface GrowthStats {
  small: number
  normal: number
  large: number
  /** 可测但未做月度评价的数量（缺少养殖月数或评价配置不可用） */
  unassessed: number
  detectedCount: number
  measurableCount: number
  unmeasurableCount: number
}

export interface GrowthSummary {
  avgBodyLengthCm: number
  avgWeightG: number
}

export interface GrowthDetectionBBox {
  x: number
  y: number
  width: number
  height: number
}

export interface GrowthImageMeta {
  src: string
  width: number
  height: number
}

export interface GrowthDetectionItem {
  id: string
  index: number
  status: GrowthStatus
  statusText: string
  confidence: number
  bbox: GrowthDetectionBBox
  bodyLengthCm: number
  weightG: number
  labelText: string
  maskPolygons: number[][]
  className?: string | null
  isMeasurable: boolean
  measurabilityLabel: string
  measurementMethod?: string | null
  measurementConfidence?: number | null
  visibleMaskLengthCm?: number | null
  measurementReasons?: string[] | null
}

export interface GrowthAssessment {
  /** 养殖月数（从投苗日起，3–15） */
  cultureMonth: number | null
  /** 投苗时平均全长（cm） */
  stockingAvgLengthCm: number | null
  /** 当月综合参考全长（cm）= 投苗体长 + 该月预期累计增长量 */
  referenceLengthCm: number | null
  /** 偏小下限（cm），低于该值判为偏小 */
  smallThresholdCm: number | null
  /** 偏大上限（cm），高于该值判为偏大 */
  largeThresholdCm: number | null
  /** 群体评价平均全长（cm），已去掉一条极端值后求平均 */
  trimmedMeanLengthCm: number | null
  /** 全部可测鱼平均全长（cm），不去极端值 */
  allMeasurableAvgLengthCm: number | null
  cohortStatus: GrowthCohortStatus
  /** 有效可测样本是否达到群体评价最小数量 */
  sampleSufficient: boolean
  /** 后端确定性规则生成的管理建议文案，不含具体投喂克数 */
  advice: string
}

export interface GrowthDetectResponse {
  taskStatus: Extract<GrowthTaskStatus, 'success' | 'failed'>
  image: GrowthImageMeta | null
  detections: GrowthDetectionItem[]
  selectedDetectionId: string | null
  stats: GrowthStats
  summary: GrowthSummary
  errorCode: GrowthDetectErrorCode | null
  /** 月度生长评价结果；缺少月份参数或评价配置不可用时为 null（此时测量结果仍有效） */
  assessment?: GrowthAssessment | null
}

/** 轻量重评请求中的单鱼测量输入，只带标识、可测性与体长，不含图片与掩码 */
export interface GrowthFishMeasurementInput {
  id: string
  isMeasurable: boolean
  bodyLengthCm: number
}

export interface GrowthEvaluateRequest {
  cultureMonth: number | null
  stockingAvgLengthCm: number | null
  fishMeasurements: GrowthFishMeasurementInput[]
}

/** 轻量重评返回的单鱼状态，用于合并覆盖当前检测项的 status / statusText */
export interface GrowthEvaluatedFishItem {
  id: string
  status: GrowthStatus
  statusText: string
}

export interface GrowthEvaluateResponse {
  detections: GrowthEvaluatedFishItem[]
  stats: GrowthStats
  summary: GrowthSummary
  assessment: GrowthAssessment | null
}

export interface GrowthVideoMeta {
  filename: string
  durationSec: number
}

export interface GrowthVideoFrameItem {
  frameId: string
  timestampSec: number
  image: GrowthImageMeta
  detections: GrowthDetectionItem[]
  selectedDetectionId: string | null
  stats: GrowthStats
  summary: GrowthSummary
  assessment?: GrowthAssessment | null
  frameStatus: GrowthVideoFrameStatus
}

export interface GrowthVideoFrameMeasurementInput {
  frameId: string
  fishMeasurements: GrowthFishMeasurementInput[]
}

export interface GrowthEvaluateVideoRequest {
  cultureMonth: number | null
  stockingAvgLengthCm: number | null
  frames: GrowthVideoFrameMeasurementInput[]
}

export interface GrowthVideoFrameEvaluationResponse {
  frameId: string
  detections: GrowthEvaluatedFishItem[]
  stats: GrowthStats
  summary: GrowthSummary
  assessment: GrowthAssessment | null
  frameStatus: GrowthVideoFrameStatus
}

export interface GrowthEvaluateVideoResponse {
  frames: GrowthVideoFrameEvaluationResponse[]
  assessment: GrowthAssessment | null
  summary: GrowthSummary
  errorCode: string | null
}

export interface GrowthVideoDetectCreateResponse {
  taskId: string
  taskStatus: Extract<GrowthVideoTaskStatus, 'queued' | 'processing'>
}

export interface GrowthVideoDetectResultResponse {
  taskId: string
  taskStatus: GrowthVideoTaskStatus
  stage: GrowthVideoTaskStage
  progress: number
  video: GrowthVideoMeta | null
  cultureMonth: number | null
  stockingAvgLengthCm: number | null
  selectedFrameId: string | null
  frames: GrowthVideoFrameItem[]
  aggregateStats: GrowthStats
  aggregateSummary: GrowthSummary
  assessment: GrowthAssessment | null
  plannedFrameCount: number
  completedFrameCount: number
  evaluableFrameCount: number
  detectionOccurrenceCount: number
  measurableOccurrenceCount: number
  isPartial: boolean
  warningCode: string | null
  errorCode: GrowthVideoDetectErrorCode | null
  createdAt?: number | null
  finishedAt?: number | null
}
