import api from '@/utils/http'
import type {
  GrowthDetectResponse,
  GrowthEvaluateRequest,
  GrowthEvaluateResponse,
  GrowthEvaluateVideoRequest,
  GrowthEvaluateVideoResponse,
  GrowthAssessmentParams,
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

/**
 * 提交图片进行生长识别，可选携带养殖月数与投苗平均全长以触发月度生长评价。
 * assessment 参数缺省时后端仅返回体长测量结果，可测鱼状态为“未评估”。
 * 该请求会在后端运行分割与分类模型，耗时较长且不自动重试。
 */
export async function detectGrowth(
  img: string | Blob,
  assessment?: GrowthAssessmentParams
): Promise<GrowthDetectResponse> {
  let base64Data: string

  if (img instanceof Blob) {
    const dataUrl = await blobToBase64(img)
    base64Data = dataUrl.split(',')[1]
  } else {
    base64Data = img.includes(',') ? img.split(',')[1] : img
  }

  return api.post<GrowthDetectResponse>({
    url: '/api/growth/detect',
    data: {
      image: base64Data,
      cultureMonth: assessment?.cultureMonth ?? null,
      stockingAvgLengthCm: assessment?.stockingAvgLengthCm ?? null
    },
    // 图片识别包含分割、分类和几何测长，按方案 §13 放宽到 90 秒；其他请求仍为 15 秒。
    timeout: 90_000
  })
}

/**
 * 轻量重评：仅用已有的单鱼测量结果与新的月份参数重算生长状态。
 * 后端不会重新加载模型、不读取图片、不重复测长，因此超时按方案 §13 设为 10 秒且不重试。
 * 失败时调用方需保留上一次成功的参数与结论，不能用失败结果覆盖当前展示。
 */
export async function evaluateGrowth(
  payload: GrowthEvaluateRequest,
  options?: { signal?: AbortSignal; showErrorMessage?: boolean }
): Promise<GrowthEvaluateResponse> {
  return api.post<GrowthEvaluateResponse>({
    url: '/api/growth/evaluate',
    data: payload,
    timeout: 10_000,
    signal: options?.signal,
    showErrorMessage: options?.showErrorMessage ?? false
  })
}

export async function uploadGrowthVideo(file: File): Promise<GrowthVideoDetectCreateResponse> {
  return uploadGrowthVideoWithAssessment(file)
}

export async function uploadGrowthVideoWithAssessment(
  file: File,
  assessment?: GrowthAssessmentParams
): Promise<GrowthVideoDetectCreateResponse> {
  const formData = new FormData()
  formData.append('file', file)
  if (assessment?.cultureMonth !== undefined && assessment.cultureMonth !== null) {
    formData.append('cultureMonth', String(assessment.cultureMonth))
  }
  if (assessment?.stockingAvgLengthCm !== undefined && assessment.stockingAvgLengthCm !== null) {
    formData.append('stockingAvgLengthCm', String(assessment.stockingAvgLengthCm))
  }

  return api.post<GrowthVideoDetectCreateResponse>({
    url: '/api/growth/detect/video',
    data: formData,
    timeout: 30_000
  })
}

export async function getGrowthVideoTask(taskId: string): Promise<GrowthVideoDetectResultResponse> {
  return api.get<GrowthVideoDetectResultResponse>({
    url: `/api/growth/detect/video/${taskId}`
  })
}

export async function cancelGrowthVideoTask(
  taskId: string
): Promise<GrowthVideoDetectResultResponse> {
  return api.post<GrowthVideoDetectResultResponse>({
    url: `/api/growth/detect/video/${taskId}/cancel`,
    data: {},
    timeout: 10_000
  })
}

export async function deleteGrowthVideoTask(
  taskId: string
): Promise<GrowthVideoDetectResultResponse> {
  return api.del<GrowthVideoDetectResultResponse>({
    url: `/api/growth/detect/video/${taskId}`
  })
}

export async function evaluateGrowthVideo(
  payload: GrowthEvaluateVideoRequest,
  options?: { signal?: AbortSignal }
): Promise<GrowthEvaluateVideoResponse> {
  return api.post<GrowthEvaluateVideoResponse>({
    url: '/api/growth/evaluate/video',
    data: payload,
    timeout: 10_000,
    signal: options?.signal,
    showErrorMessage: false
  })
}

export async function getCameraStream(): Promise<string> {
  return api.get<string>({ url: '/api/growth/camera/stream' })
}
