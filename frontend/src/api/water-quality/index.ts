import request from '@/utils/http'
import type { WaterQualityData, WaterQualityThreshold } from '@/types/water-quality'

interface WaterQualityApiRecord {
  id: number | string
  pond_id: string
  temperature: number
  ph_value: number
  dissolved_oxygen: number
  ammonia_nitrogen: number
  nitrite: number
  collect_time: string
  status: string
}

interface WaterQualityHistoryParams {
  pageNum?: number
  pageSize?: number
  startTime?: string
  endTime?: string
  pondId?: string
}

interface WaterQualityHistoryResponse {
  data: WaterQualityApiRecord[]
  total: number
}

function normalizeWaterQuality(item: WaterQualityApiRecord): WaterQualityData {
  return {
    id: String(item.id ?? ''),
    temperature: item.temperature,
    ph: item.ph_value,
    dissolvedOxygen: item.dissolved_oxygen,
    ammoniaNitrogen: item.ammonia_nitrogen,
    nitrite: item.nitrite,
    collectTime: item.collect_time,
    status: item.status === '正常' ? 'normal' : 'warning'
  }
}

export function getLatestWaterQuality(pondId?: string): Promise<WaterQualityData> {
  return request
    .get<WaterQualityApiRecord>({
      url: '/api/water-quality/latest',
      params: { pond_id: pondId }
    })
    .then((res) => normalizeWaterQuality(res))
}

export function getWaterQualityHistory(
  params: WaterQualityHistoryParams
): Promise<{ list: WaterQualityData[]; total: number }> {
  return request
    .get<WaterQualityHistoryResponse>({
      url: '/api/water-quality/history',
      params: {
        start_time: params.startTime,
        end_time: params.endTime,
        pond_id: params.pondId,
        page_num: params.pageNum || 1,
        page_size: params.pageSize || 10
      }
    })
    .then((res) => ({
      list: res.data.map((item) => normalizeWaterQuality(item)),
      total: res.total
    }))
}

export function getThresholdConfig(): Promise<WaterQualityThreshold> {
  return request
    .get<Record<string, { min: number; max: number }>>({
      url: '/api/water-quality/threshold'
    })
    .then((res) => ({
      temperature: res.temperature,
      ph: res.ph,
      dissolvedOxygen: res.dissolved_oxygen,
      ammoniaNitrogen: res.ammonia_nitrogen,
      nitrite: res.nitrite
    }))
}
