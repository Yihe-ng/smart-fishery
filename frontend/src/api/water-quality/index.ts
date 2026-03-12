import type { PageResult, PageQuery } from '@/types'
import type { WaterQualityData, WaterQualityThreshold } from '@/types/water-quality'

// 获取最新水质数据（预留接口）
// TODO: [后端接入] 此处为模拟数据，需替换为真实后端接口
export function getLatestWaterQuality(): Promise<WaterQualityData> {
  // TODO: 接入后端
  // return request.get('/water-quality/latest')
  return Promise.resolve({
    id: '1',
    temperature: 25.5,
    ph: 7.2,
    dissolvedOxygen: 6.8,
    ammoniaNitrogen: 0.3,
    nitrite: 0.05,
    collectTime: new Date().toISOString(),
    status: 'normal'
  })
}

// 获取历史数据（预留接口）
export function getWaterQualityHistory(
  params: PageQuery & { startTime?: string; endTime?: string }
): Promise<PageResult<WaterQualityData>> {
  console.log('getWaterQualityHistory params:', params)
  // TODO: 接入后端
  return Promise.resolve({
    list: [
      {
        id: '1',
        temperature: 25.5,
        ph: 7.2,
        dissolvedOxygen: 6.8,
        ammoniaNitrogen: 0.3,
        nitrite: 0.05,
        collectTime: new Date().toISOString(),
        status: 'normal'
      }
    ],
    total: 1
  })
}

// 获取阈值配置（预留接口）
// TODO: [后端接入] 此处为模拟数据，需替换为真实后端接口
export function getThresholdConfig(): Promise<WaterQualityThreshold> {
  // TODO: 接入后端
  // return request.get('/water-quality/threshold')
  return Promise.resolve({
    temperature: { min: 20, max: 28 },
    ph: { min: 6.5, max: 8.5 },
    dissolvedOxygen: { min: 5, max: 15 },
    ammoniaNitrogen: { min: 0, max: 0.5 },
    nitrite: { min: 0, max: 0.1 }
  })
}
