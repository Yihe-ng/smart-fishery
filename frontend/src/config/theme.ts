export type WaterQualityMetricKey =
  | 'temperature'
  | 'ph'
  | 'dissolvedOxygen'
  | 'ammoniaNitrogen'
  | 'nitrite'

export interface WaterQualityMetricMeta {
  key: WaterQualityMetricKey
  label: string
  unit: string
  icon: string
  color: `#${string}`
  colorVar: `--${string}`
}

export const WATER_QUALITY_METRICS: Record<WaterQualityMetricKey, WaterQualityMetricMeta> = {
  temperature: {
    key: 'temperature',
    label: '水温',
    unit: '℃',
    icon: 'ri:temp-hot-line',
    color: '#C77657',
    colorVar: '--metric-temperature'
  },
  ph: {
    key: 'ph',
    label: 'pH值',
    unit: '',
    icon: 'ri:test-tube-line',
    color: '#6D63D9',
    colorVar: '--metric-ph'
  },
  dissolvedOxygen: {
    key: 'dissolvedOxygen',
    label: '溶解氧',
    unit: 'mg/L',
    icon: 'ri:windy-line',
    color: '#57B7C9',
    colorVar: '--metric-oxygen'
  },
  ammoniaNitrogen: {
    key: 'ammoniaNitrogen',
    label: '氨氮',
    unit: 'mg/L',
    icon: 'ri:flask-line',
    color: '#C9A24A',
    colorVar: '--metric-ammonia'
  },
  nitrite: {
    key: 'nitrite',
    label: '亚硝酸盐',
    unit: 'mg/L',
    icon: 'ri:drop-line',
    color: '#D35A5F',
    colorVar: '--metric-nitrite'
  }
}

export const WATER_QUALITY_METRIC_ORDER = Object.keys(
  WATER_QUALITY_METRICS
) as WaterQualityMetricKey[]

export function getWaterQualityMetricColor(metric: WaterQualityMetricKey) {
  // ECharts canvas 对 CSS 变量和 OKLCH 颜色支持不稳定，图表侧统一使用 hex。
  return WATER_QUALITY_METRICS[metric].color
}
