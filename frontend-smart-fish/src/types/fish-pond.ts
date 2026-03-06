export type PondStatus = 'running' | 'stopped' | 'maintenance'

export interface FishPond {
  id: string
  name: string // 池子名称（如：试验池 A）
  code: string // 编号（如：P001）
  volume: number // 容积（立方米）
  fishType: string // 养殖鱼类
  fishCount: number // 鱼数量
  status: PondStatus
  createTime: string
  updateTime: string
  remark?: string
  config?: Record<string, any> // 预留扩展字段
}

export interface PondQuery {
  page?: number
  pageSize?: number
  keyword?: string
  status?: PondStatus
}
