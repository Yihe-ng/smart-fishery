export interface WaterQualityData {
  id: string
  temperature: number // 水温 ℃
  ph: number // pH值
  dissolvedOxygen: number // 溶解氧 mg/L
  ammoniaNitrogen: number // 氨氮 mg/L
  nitrite: number // 亚硝酸盐 mg/L
  collectTime: string
  status: 'normal' | 'warning' | 'danger' // 综合状态
}

export interface WaterQualityThreshold {
  temperature: { min: number; max: number }
  ph: { min: number; max: number }
  dissolvedOxygen: { min: number; max: number }
  ammoniaNitrogen: { min: number; max: number }
  nitrite: { min: number; max: number }
}
