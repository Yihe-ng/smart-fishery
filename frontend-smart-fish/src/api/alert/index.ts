import type { PageResult, PageQuery } from '@/types'
import type { Alert } from '@/types/alert'

// 获取最近告警
// TODO: [后端接入] 此处为模拟数据，需替换为真实后端接口
export function getRecentAlerts(count: number = 5): Promise<Alert[]> {
  // 模拟数据返回，请替换为 axios.get('/alert/recent', { params: { count } })
  const data: Alert[] = [
    {
      id: '1',
      type: 'water_quality',
      level: 'warning',
      title: '水温偏高',
      message: '当前水温 28.5℃，超过阈值 28.0℃',
      createTime: new Date().toISOString(),
      status: 'pending',
      relatedDevice: 'temp-001'
    },
    {
      id: '2',
      type: 'device_offline',
      level: 'critical',
      title: '传感器离线',
      message: '亚硝酸盐传感器已离线',
      createTime: new Date().toISOString(),
      status: 'pending',
      relatedDevice: 'no2-001'
    }
  ]
  return Promise.resolve(data.slice(0, count))
}

// 获取告警列表 (兼容旧调用)
export function getAlertList(params: PageQuery): Promise<PageResult<Alert>> {
  return getAllAlerts(params)
}

// 获取所有告警（分页）
export function getAllAlerts(params: PageQuery): Promise<PageResult<Alert>> {
  console.log('getAllAlerts params:', params)
  return Promise.resolve({
    list: [],
    total: 0
  })
}

// 确认/忽略告警
export function resolveAlert(id: string): Promise<boolean> {
  console.log('resolveAlert id:', id)
  return Promise.resolve(true)
}
