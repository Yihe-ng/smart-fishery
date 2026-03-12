export interface FeedingConfig {
  feedCoefficient: number // 饲料系数 1.8-1.4
  frequency: number // 每日投喂次数
  feedSize: string // 饲料粒径
}

export interface FeedingLog {
  id: string
  feedTime: string
  amount: number // 投喂量(g)
  status: 'completed' | 'failed' | 'pending'
  triggerType: 'auto' | 'manual' // 自动/手动
}

export interface FeedingDevice {
  id: string
  name: string
  status: 'online' | 'offline'
  feedRemaining?: number // 料仓余量（预留）
}
