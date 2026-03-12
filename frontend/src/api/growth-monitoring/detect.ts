import type { GrowthDetectResponse } from '@/types/growth-monitoring'

/**
 * 生长识别检测接口
 * @param img - 图像数据（base64 或 Blob）
 * @returns 检测结果
 */
// TODO: [后端接入] 此处为模拟数据，需替换为真实后端接口
export async function detectGrowth(img: string | Blob): Promise<GrowthDetectResponse> {
  // TODO: 替换为真实后端接口
  if (import.meta.env.DEV) console.log('调用生长识别接口', img ? 'image provided' : 'no image')
  
  // 模拟生成随机数据
  const generateMockDetection = () => {
    const weight = Math.floor(Math.random() * (1500 - 300) + 300) // 300-1500g
    const length = Math.floor(Math.random() * (50 - 20) + 20) // 20-50cm
    let status: 'small' | 'normal' | 'large' = 'normal'
    
    if (weight < 500) status = 'small'
    else if (weight > 1000) status = 'large'
    
    return {
      class: status,
      confidence: Number((Math.random() * (0.99 - 0.8) + 0.8).toFixed(2)),
      bbox: [
        Math.floor(Math.random() * 200),
        Math.floor(Math.random() * 200),
        Math.floor(Math.random() * 200 + 100),
        Math.floor(Math.random() * 200 + 100)
      ] as [number, number, number, number],
      bodyLength: length,
      weight: weight
    }
  }

  // 模拟 1-3 个检测结果
  const detections = Array.from({ length: Math.floor(Math.random() * 3) + 1 }, generateMockDetection)

  return Promise.resolve({
    detections
  })
}

/**
 * 获取摄像头视频流
 * @returns HLS 视频流 URL
 */
export async function getCameraStream(): Promise<string> {
  if (import.meta.env.DEV) console.log('获取摄像头视频流')
  return Promise.resolve('http://devimages.apple.com/iphone/samples/bipbop/gear1/prog_index.m3u8')
}
