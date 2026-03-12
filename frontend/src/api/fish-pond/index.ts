import request from '@/utils/http'
import type { PageResult, PageQuery, FishPond } from '@/types'

/** 获取试验池列表 */
export function getPondList(params: PageQuery): Promise<PageResult<FishPond>> {
  return request.get({ url: '/fish-pond/list', params })
}

/** 获取试验池详情 */
export function getPondDetail(id: string): Promise<FishPond> {
  return request.get({ url: `/fish-pond/detail/${id}` })
}

/** 创建试验池 */
export function createPond(data: Partial<FishPond>): Promise<any> {
  return request.post({ url: '/fish-pond/create', data, showSuccessMessage: true })
}

/** 更新试验池 */
export function updatePond(data: Partial<FishPond>): Promise<any> {
  return request.put({ url: '/fish-pond/update', data, showSuccessMessage: true })
}

/** 删除试验池 */
export function deletePond(id: string): Promise<any> {
  return request.del({ url: `/fish-pond/delete/${id}`, showSuccessMessage: true })
}
