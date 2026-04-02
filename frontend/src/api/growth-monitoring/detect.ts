import api from '@/utils/http'
import type {
  GrowthDetectResponse,
  GrowthVideoDetectCreateResponse,
  GrowthVideoDetectResultResponse
} from '@/types/growth-monitoring'

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

  return api.post<GrowthDetectResponse>({
    url: '/api/growth/detect',
    params: { image: base64Data }
  })
}

export async function uploadGrowthVideo(file: File): Promise<GrowthVideoDetectCreateResponse> {
  const formData = new FormData()
  formData.append('file', file)

  return api.post<GrowthVideoDetectCreateResponse>({
    url: '/api/growth/detect/video',
    data: formData
  })
}

export async function getGrowthVideoTask(taskId: string): Promise<GrowthVideoDetectResultResponse> {
  return api.get<GrowthVideoDetectResultResponse>({
    url: `/api/growth/detect/video/${taskId}`
  })
}

export async function getCameraStream(): Promise<string> {
  return api.get<string>({ url: '/api/growth/camera/stream' })
}
