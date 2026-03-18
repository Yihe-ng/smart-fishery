import request from '@/utils/http'

import type { PageResult, PageQuery } from '@/types'
import type { FeedingConfig, FeedingLog } from '@/types/feeding'

interface BackendFeedingConfig {
  feed_coefficient: number
  frequency: number
  feed_size: string
}

interface BackendFeedingLog {
  id: string
  feed_time: string
  amount: number
  status: FeedingLog['status']
  trigger_type: FeedingLog['triggerType']
}

function mapFeedingConfig(config: BackendFeedingConfig): FeedingConfig {
  return {
    feedCoefficient: config.feed_coefficient,
    frequency: config.frequency,
    feedSize: config.feed_size,
  }
}

function mapFeedingLog(log: BackendFeedingLog): FeedingLog {
  return {
    id: log.id,
    feedTime: log.feed_time,
    amount: log.amount,
    status: log.status,
    triggerType: log.trigger_type,
  }
}

export function getFeedingConfig(): Promise<FeedingConfig> {
  return request
    .get<BackendFeedingConfig>({
      url: '/api/feeding/config',
    })
    .then(mapFeedingConfig)
}

export function updateFeedingConfig(config: FeedingConfig): Promise<boolean> {
  return request
    .post<{ updated: boolean }>({
      url: '/api/feeding/config',
      data: {
        feed_coefficient: config.feedCoefficient,
        frequency: config.frequency,
        feed_size: config.feedSize,
      },
    })
    .then((response) => response.updated)
}

export function getFeedingLogs(params: PageQuery): Promise<PageResult<FeedingLog>> {
  return request
    .get<PageResult<BackendFeedingLog>>({
      url: '/api/feeding/logs',
      params: {
        pageNum: params.current,
        pageSize: params.size,
      },
    })
    .then((result) => ({
      total: result.total,
      list: result.list.map(mapFeedingLog),
    }))
}

export function manualFeeding(amount: number): Promise<boolean> {
  return request
    .post<{ id: string; amount: number }>({
      url: '/api/feeding/manual',
      params: { amount },
    })
    .then(() => true)
}
