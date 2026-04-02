export type GrowthTaskStatus = 'idle' | 'uploading' | 'processing' | 'success' | 'failed'
export type GrowthVideoTaskStatus = 'queued' | 'processing' | 'success' | 'failed'

export type GrowthStatus = 'small' | 'normal' | 'large'

export type GrowthDetectErrorCode =
  | 'INVALID_IMAGE'
  | 'IMAGE_TOO_LARGE'
  | 'IMAGE_DECODE_FAILED'
  | 'NO_FISH_DETECTED'
  | 'MODEL_INFERENCE_FAILED'
  | 'INTERNAL_ERROR'

export type GrowthVideoDetectErrorCode =
  | 'INVALID_VIDEO'
  | 'VIDEO_TOO_LARGE'
  | 'VIDEO_DECODE_FAILED'
  | 'NO_VALID_FRAMES'
  | 'MODEL_INFERENCE_FAILED'
  | 'INTERNAL_ERROR'

export interface GrowthStats {
  small: number
  normal: number
  large: number
  detectedCount: number
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
}

export interface GrowthDetectResponse {
  taskStatus: Extract<GrowthTaskStatus, 'success' | 'failed'>
  image: GrowthImageMeta | null
  detections: GrowthDetectionItem[]
  selectedDetectionId: string | null
  stats: GrowthStats
  summary: GrowthSummary
  errorCode: GrowthDetectErrorCode | null
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
}

export interface GrowthVideoDetectCreateResponse {
  taskId: string
  taskStatus: Extract<GrowthVideoTaskStatus, 'queued' | 'processing'>
}

export interface GrowthVideoDetectResultResponse {
  taskId: string
  taskStatus: GrowthVideoTaskStatus
  progress: number
  video: GrowthVideoMeta | null
  selectedFrameId: string | null
  frames: GrowthVideoFrameItem[]
  aggregateStats: GrowthStats
  aggregateSummary: GrowthSummary
  errorCode: GrowthVideoDetectErrorCode | null
}
