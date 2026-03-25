import type { Alert } from '@/types/alert'
import type { SensorDevice } from '@/types/device'
import type { WaterQualityMetricKey } from '@/config/theme'

export interface WaterQualityData {
  id: string
  temperature: number
  ph: number
  dissolvedOxygen: number
  ammoniaNitrogen: number
  nitrite: number
  collectTime: string
  status: 'normal' | 'warning' | 'danger'
}

export interface ThresholdRange {
  min?: number
  max?: number
}

export interface WaterQualityThresholdRule {
  label: string
  unit: string
  ideal: ThresholdRange
  warning: ThresholdRange
  critical: ThresholdRange
}

export type WaterQualityThreshold = Record<WaterQualityMetricKey, WaterQualityThresholdRule>

export type MetricStatusText = '正常' | '警戒' | '危险'

export interface DashboardFrameMetric {
  key: WaterQualityMetricKey
  label: string
  value: number
  unit: string
  statusText: MetricStatusText
  trendText: string
  isIdeal: boolean
}

export interface DashboardFrameResponse {
  index: number
  nextIndex: number
  total: number
  hasNext: boolean
  collectTime: string | null
  waterQuality: WaterQualityData | null
  previousWaterQuality: WaterQualityData | null
  metrics: Record<WaterQualityMetricKey, DashboardFrameMetric>
  devices: SensorDevice[]
  alerts: Alert[]
}
