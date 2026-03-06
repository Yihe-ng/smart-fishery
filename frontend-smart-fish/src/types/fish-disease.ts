export interface DetectionResult {
  id: string
  imageUrl: string // 抓拍图片URL
  detectTime: string
  confidence: number // 置信度 0-100
  diseaseType: 'gill_rot' | 'red_skin' | 'enteritis' | 'healthy'
  bbox?: {
    // 边界框坐标
    x: number
    y: number
    width: number
    height: number
  }
}

export interface HealthOverview {
  score: number // 健康评分 0-100
  risks: {
    gillRot: 'low' | 'medium' | 'high'
    redSkin: 'low' | 'medium' | 'high'
    enteritis: 'low' | 'medium' | 'high'
  }
}

// 兼容病害识别模块的类型
export interface DiseaseStats {
  烂鳃: number
  赤皮: number
  肠炎: number
}

export interface DetectResponse {
  detections: {
    class: string
    confidence: number
    bbox: [number, number, number, number]
  }[]
}
