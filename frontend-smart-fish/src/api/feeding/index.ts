import type { PageResult, PageQuery } from '@/types'
import type { FeedingConfig, FeedingLog } from '@/types/feeding'

// 获取投喂配置
// TODO: [后端接入] 此处为模拟数据，需替换为真实后端接口
export function getFeedingConfig(): Promise<FeedingConfig> {
  // 模拟数据返回，请替换为 axios.get('/feeding/config')
  return Promise.resolve({
    feedCoefficient: 1.6,
    frequency: 3,
    feedSize: '2.0mm'
  })
}

// 更新投喂配置
// TODO: [后端接入] 此处为模拟数据，需替换为真实后端接口
export function updateFeedingConfig(config: FeedingConfig): Promise<boolean> {
  console.log('updateFeedingConfig:', config)
  // 模拟成功返回，请替换为 axios.post('/feeding/config', config)
  return Promise.resolve(true)
}

// 获取投喂日志
// TODO: [后端接入] 此处为模拟数据，需替换为真实后端接口
export function getFeedingLogs(params: PageQuery): Promise<PageResult<FeedingLog>> {
  console.log('getFeedingLogs params:', params)
  // 模拟数据返回，请替换为 axios.get('/feeding/logs', { params })
  return Promise.resolve({
    list: [
      {
        id: '1',
        feedTime: '2024-03-20 08:00:00',
        amount: 500,
        status: 'completed',
        triggerType: 'auto'
      },
      {
        id: '2',
        feedTime: '2024-03-20 12:00:00',
        amount: 500,
        status: 'completed',
        triggerType: 'auto'
      },
      {
        id: '3',
        feedTime: '2024-03-20 18:00:00',
        amount: 600,
        status: 'pending',
        triggerType: 'manual'
      }
    ],
    total: 3
  })
}

// 手动投喂
export function manualFeeding(amount: number): Promise<boolean> {
  console.log('manualFeeding amount:', amount)
  return Promise.resolve(true)
}
