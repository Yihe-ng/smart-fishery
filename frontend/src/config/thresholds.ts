export interface ThresholdRule {
  min?: number
  max?: number
  label: string
  unit?: string
}

export const WATER_QUALITY_THRESHOLDS: Record<string, ThresholdRule> = {
  temperature: { min: 22.0, max: 32.0, label: '水温', unit: '℃' },
  dissolvedOxygen: { min: 5.0, label: '溶解氧', unit: 'mg/L' },
  ammoniaNitrogen: { max: 0.2, label: '氨氮', unit: 'mg/L' },
  nitrite: { max: 0.1, label: '亚硝酸盐', unit: 'mg/L' },
  ph: { min: 7.8, max: 8.5, label: 'pH值', unit: '' }
}
