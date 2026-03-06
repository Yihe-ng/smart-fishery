export interface GrowthStats {
  small: number
  normal: number
  large: number
}

export interface GrowthDetectionItem {
  class: 'small' | 'normal' | 'large'
  confidence: number
  bbox: [number, number, number, number]
  bodyLength: number
  weight: number
}

export interface GrowthDetectResponse {
  detections: GrowthDetectionItem[]
}
