import type { SensorDevice } from '@/types/device'

// 获取所有传感器设备
// TODO: [后端接入] 此处为模拟数据，需替换为真实后端接口
export function getSensorDevices(): Promise<SensorDevice[]> {
  // 模拟数据返回，请替换为 axios.get('/device/list')
  return Promise.resolve([
    {
      id: 'temp-001',
      name: '水温传感器',
      type: 'temperature',
      status: 'online',
      lastOnlineTime: new Date().toISOString(),
      lastData: 25.5,
      unit: '℃',
      location: '1号池东侧'
    },
    {
      id: 'ph-001',
      name: 'pH传感器',
      type: 'ph',
      status: 'online',
      lastOnlineTime: new Date().toISOString(),
      lastData: 7.2,
      unit: '',
      location: '1号池中心'
    },
    {
      id: 'do-001',
      name: '溶氧传感器',
      type: 'dissolved_oxygen',
      status: 'online',
      lastOnlineTime: new Date().toISOString(),
      lastData: 6.8,
      unit: 'mg/L',
      location: '1号池西侧'
    },
    {
      id: 'nh3-001',
      name: '氨氮传感器',
      type: 'ammonia_nitrogen',
      status: 'online',
      lastOnlineTime: new Date().toISOString(),
      lastData: 0.3,
      unit: 'mg/L',
      location: '总进水口'
    },
    {
      id: 'no2-001',
      name: '亚硝酸盐传感器',
      type: 'nitrite',
      status: 'offline',
      lastOnlineTime: new Date().toISOString(),
      lastData: 0.05,
      unit: 'mg/L',
      location: '总出水口'
    }
  ])
}
