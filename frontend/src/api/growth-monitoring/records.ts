import api from '@/utils/http'
import type {
  GrowthRecordAssessmentUpdatePayload,
  GrowthRecordItem,
  GrowthRecordSavePayload,
  GrowthRecordSourceType
} from '@/types/growth-monitoring'

export interface GrowthRecordHistoryParams {
  pageNum?: number
  pageSize?: number
  pondId?: string
  sourceType?: GrowthRecordSourceType
  startTime?: string
  endTime?: string
}

interface GrowthRecordHistoryResponse {
  data: GrowthRecordItem[]
  total: number
}

/** 识别成功后保存一条可测摘要记录，返回含 id 的落库结果 */
export function saveGrowthRecord(payload: GrowthRecordSavePayload): Promise<GrowthRecordItem> {
  return api.post<GrowthRecordItem>({
    url: '/api/growth/records',
    data: payload,
    timeout: 10_000,
    showErrorMessage: false
  })
}

/** 轻量重评成功后仅更新记录的月度评价字段，不产生新的历史行 */
export function updateGrowthRecordAssessment(
  recordId: number,
  payload: GrowthRecordAssessmentUpdatePayload
): Promise<GrowthRecordItem> {
  return api.put<GrowthRecordItem>({
    url: `/api/growth/records/${recordId}`,
    data: payload,
    timeout: 10_000,
    showErrorMessage: false
  })
}

export function getGrowthRecords(
  params: GrowthRecordHistoryParams
): Promise<{ list: GrowthRecordItem[]; total: number }> {
  return api
    .get<GrowthRecordHistoryResponse>({
      url: '/api/growth/records',
      params: {
        pond_id: params.pondId || undefined,
        source_type: params.sourceType || undefined,
        start_time: params.startTime,
        end_time: params.endTime,
        page_num: params.pageNum || 1,
        page_size: params.pageSize || 10
      }
    })
    .then((res) => ({ list: res.data, total: res.total }))
}

/** 某池塘最近一次识别记录；无记录时返回 null */
export function getLatestGrowthRecord(pondId?: string): Promise<GrowthRecordItem | null> {
  return api.get<GrowthRecordItem | null>({
    url: '/api/growth/records/latest',
    params: { pond_id: pondId || undefined },
    timeout: 10_000,
    showErrorMessage: false
  })
}

export function deleteGrowthRecord(recordId: number): Promise<void> {
  return api.del<void>({
    url: `/api/growth/records/${recordId}`,
    timeout: 10_000
  })
}
