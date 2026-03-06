export interface SensorDevice {
  id: string
  name: string // 传感器名称
  type: SensorType
  status: 'online' | 'offline' | 'error'
  lastOnlineTime?: string
  lastData?: number // 最后数据值
  unit?: string // 单位
  location?: string // 安装位置
}

export type SensorType = 'temperature' | 'ph' | 'dissolved_oxygen' | 'ammonia_nitrogen' | 'nitrite'
