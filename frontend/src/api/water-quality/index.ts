import request from '@/utils/http'
import type {
  DashboardFrameResponse,
  WaterQualityData,
  WaterQualityThreshold
} from '@/types/water-quality'

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

interface DashboardFrameApiResponse {
  index: number
  nextIndex: number
  total: number
  hasNext: boolean
  collectTime: string | null
  waterQuality: DashboardFrameWaterQualityApi | null
  previousWaterQuality: DashboardFrameWaterQualityApi | null
  metrics: DashboardFrameResponse['metrics']
  devices: DashboardFrameResponse['devices']
  alerts: DashboardFrameResponse['alerts']
}

interface DashboardFrameWaterQualityApi {
  id: string
  temperature: number
  ph: number
  dissolvedOxygen: number
  ammoniaNitrogen: number
  nitrite: number
  collectTime: string
  status: string
}

function normalizeWaterQuality(item: WaterQualityApiRecord): WaterQualityData {
  const statusMap: Record<string, WaterQualityData['status']> = {
    正常: 'normal',
    警戒: 'warning',
    危险: 'danger'
  }
  return {
    id: String(item.id ?? ''),
    temperature: item.temperature,
    ph: item.ph_value,
    dissolvedOxygen: item.dissolved_oxygen,
    ammoniaNitrogen: item.ammonia_nitrogen,
    nitrite: item.nitrite,
    collectTime: item.collect_time,
    status: statusMap[item.status] ?? 'warning'
  }
}

function normalizeFrameWaterQuality(
  item: DashboardFrameWaterQualityApi | null
): WaterQualityData | null {
  if (!item) {
    return null
  }

  const statusMap: Record<string, WaterQualityData['status']> = {
    正常: 'normal',
    警戒: 'warning',
    危险: 'danger'
  }

  return {
    ...item,
    status: statusMap[item.status] ?? 'warning'
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
  return request.get<WaterQualityThreshold>({
    url: '/api/water-quality/threshold'
  })
}

export function getDashboardFrame(index: number): Promise<DashboardFrameResponse> {
  return request
    .get<DashboardFrameApiResponse>({
      url: '/api/water-quality/dashboard-frame',
      params: { index }
    })
    .then((res) => ({
      ...res,
      waterQuality: normalizeFrameWaterQuality(res.waterQuality),
      previousWaterQuality: normalizeFrameWaterQuality(res.previousWaterQuality)
    }))
}
