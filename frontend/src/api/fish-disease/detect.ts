import type { DetectResponse } from '@/types/fish-disease'

/**
 * 病害检测接口
 * @param img - 图像数据（base64 或 Blob）
 * @returns 检测结果
 */
// TODO: [后端接入] 此处为模拟数据，需替换为真实后端接口
export async function detectDisease(img: string | Blob): Promise<DetectResponse> {
  // TODO: 替换为真实后端接口，例如：
  // const formData = new FormData();
  // formData.append('image', img);
  // return request.post('/disease/detect', formData);

  console.log('调用病害检测接口', img ? 'image provided' : 'no image')
  // 模拟一些检测结果
  return Promise.resolve({
    detections: [
      {
        class: '烂鳃',
        confidence: 0.94,
        bbox: [100, 100, 200, 200]
      }
    ]
  })
}

/**
 * 获取摄像头视频流
 * @returns HLS 视频流 URL
 */
// TODO: [后端接入] 此处为模拟数据，需替换为真实后端接口
export async function getCameraStream(): Promise<string> {
  // TODO: 替换为真实摄像头流 API，例如：return request.get('/camera/stream')
  console.log('获取摄像头视频流')
  // 返回一个公共的 HLS 测试流，用于前端展示
  // return Promise.resolve('https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8')
  return Promise.resolve('http://devimages.apple.com/iphone/samples/bipbop/gear1/prog_index.m3u8')
}

/**
 * 获取健康总览数据
 */
// TODO: [后端接入] 此处为模拟数据，需替换为真实后端接口
export async function getHealthOverview(): Promise<any> {
  // 模拟数据返回，请替换为 axios.get('/health/overview')
  return Promise.resolve({
    score: 92,
    risks: {
      gillRot: 'low',
      redSkin: 'medium',
      enteritis: 'low'
    }
  })
}
