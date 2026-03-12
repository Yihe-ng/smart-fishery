export interface Alert {
  id: string
  type: 'water_quality' | 'device_offline' | 'disease_detected'
  level: 'critical' | 'warning' | 'info'
  title: string
  message: string
  createTime: string
  status: 'pending' | 'resolved'
  relatedDevice?: string // 关联设备ID
}
