import api from '@/utils/http'
import type { GrowthDetectResponse, GrowthDetectionItem } from '@/types/growth-monitoring'

interface RawDetectionItem {
  class_name: string
  confidence: number
  bbox: number[]
  length: number
}

interface BackendResponse {
  detections: RawDetectionItem[]
}

const CM_PER_PIXEL = 0.1

function mapClassName(className: string): 'small' | 'normal' | 'large' {
  const lower = className.toLowerCase()
  if (lower === 'small') return 'small'
  if (lower === 'medium') return 'normal'
  if (lower === 'large') return 'large'
  return 'normal'
}

function estimateWeight(lengthCm: number): number {
  return Math.round(0.01 * lengthCm ** 3)
}

function mapDetectionItem(raw: RawDetectionItem): GrowthDetectionItem {
  const bodyLength = Math.round(raw.length * CM_PER_PIXEL)
  return {
    class: mapClassName(raw.class_name),
    confidence: raw.confidence,
    bbox: raw.bbox as [number, number, number, number],
    bodyLength,
    weight: estimateWeight(bodyLength)
  }
}

function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onloadend = () => resolve(reader.result as string)
    reader.onerror = reject
    reader.readAsDataURL(blob)
  })
}

export async function detectGrowth(img: string | Blob): Promise<GrowthDetectResponse> {
  let base64Data: string

  if (img instanceof Blob) {
    const dataUrl = await blobToBase64(img)
    base64Data = dataUrl.split(',')[1]
  } else {
    base64Data = img.includes(',') ? img.split(',')[1] : img
  }

  const response = await api.post<BackendResponse>({
    url: '/api/growth/detect',
    params: { image: base64Data }
  })

  return {
    detections: response.detections.map(mapDetectionItem)
  }
}

export async function getCameraStream(): Promise<string> {
  return api.get<string>({ url: '/api/growth/camera/stream' })
}
