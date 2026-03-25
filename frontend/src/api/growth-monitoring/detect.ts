import api from '@/utils/http'
import type { GrowthDetectResponse, GrowthDetectionItem } from '@/types/growth-monitoring'

/**
 * 后端 YOLO 模型返回的原始检测数据结构
 */
interface RawDetectionItem {
  class_name: string // 识别类别名称，例如 'small', 'medium', 'large'
  confidence: number // 置信度 (0~1)
  bbox: number[] // 边界框坐标，格式通常为 [x, y, width, height]
  length: number // 像素长度（通过对角线或宽度计算得出）
}

/**
 * 后端检测接口的完整响应结构
 */
interface BackendResponse {
  detections: RawDetectionItem[]
}

/**
 * 像素到物理长度（厘米）的转换比例。
 * 注意：目前这是一个静态硬编码值。未来如果引入参照物或深度相机，
 * 可以将其改为动态传入的变量。
 */
const CM_PER_PIXEL = 0.1

// ---------------- 鱼类体长体重通用计算模型 ----------------
// 基于多种鱼类样本取平均值计算得出，公式为 W = a * L^b
// 在不考虑具体品种的通用监测场景下作为基准模型使用
const GENERAL_FISH_COEF_A = 0.0285 // 综合形状系数平均值
const GENERAL_FISH_COEF_B = 2.937 // 综合生长指数平均值

/**
 * 将后端的英文类别名称映射为前端统一的规格标识
 * @param className 后端返回的类别名
 * @returns 标准化的规格字符串
 */
function mapClassName(className: string): 'small' | 'normal' | 'large' {
  const lower = className.toLowerCase()
  // 提供一定的容错处理，防止大小写或相似词汇带来的匹配失败
  if (lower === 'small') return 'small'
  if (lower === 'medium' || lower === 'normal') return 'normal'
  if (lower === 'large') return 'large'
  return 'normal' // 默认兜底策略
}

/**
 * 根据体长（厘米）估算鱼的体重（克）
 * 使用非线性的幂函数模型，比简单的线性模型或三次取整更符合生物学规律
 * @param lengthCm 物理体长（厘米）
 * @returns 估算体重（克），保留一位小数
 */
function estimateWeight(lengthCm: number): number {
  if (lengthCm <= 0) return 0

  // 核心计算公式 W = a * L^b
  const weight = GENERAL_FISH_COEF_A * Math.pow(lengthCm, GENERAL_FISH_COEF_B)

  // 保留一位小数，提高前端展示的精度 (例如返回 525.4 而不是 525)
  return Math.round(weight * 10) / 10
}

/**
 * 将后端返回的单条原始检测数据，转换为前端业务组件所需的数据格式
 * @param raw 后端返回的单条记录
 * @returns 前端组件可直接消费的记录格式
 */
function mapDetectionItem(raw: RawDetectionItem): GrowthDetectionItem {
  // 计算物理体长，保留一位小数以防误差在后续三次方计算中被放大
  const bodyLength = Math.round(raw.length * CM_PER_PIXEL * 10) / 10

  return {
    class: mapClassName(raw.class_name),
    confidence: Math.round(raw.confidence * 100) / 100, // 置信度也建议保留两位小数
    bbox: raw.bbox as [number, number, number, number],
    bodyLength: bodyLength,
    weight: estimateWeight(bodyLength) // 自动推导该体长对应的估算重量
  }
}

/**
 * 辅助工具函数：将 Blob 对象（例如从 Canvas 截图获取的二进制图片）转换为 Base64 字符串
 * @param blob 二进制图像数据
 * @returns Promise 包裹的 Base64 字符串
 */
function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onloadend = () => resolve(reader.result as string)
    reader.onerror = reject
    reader.readAsDataURL(blob)
  })
}

/**
 * 核心业务方法：执行生长状况检测
 * 支持直接传入 Base64 字符串，也支持传入 File/Blob 对象
 * @param img 图像数据
 * @returns 解析并计算完成的监测报告
 */
export async function detectGrowth(img: string | Blob): Promise<GrowthDetectResponse> {
  let base64Data: string

  // 统一图片格式，方便后端统一通过 base64.b64decode 解析
  if (img instanceof Blob) {
    const dataUrl = await blobToBase64(img)
    // 剥离 data:image/jpeg;base64, 前缀，只保留纯数据部分
    base64Data = dataUrl.split(',')[1]
  } else {
    // 处理直接传入字符串的情况
    base64Data = img.includes(',') ? img.split(',')[1] : img
  }

  // 发送请求给 YOLO 推理服务
  const response = await api.post<BackendResponse>({
    url: '/api/growth/detect',
    params: { image: base64Data }
  })

  // 遍历所有检测到的目标，应用映射和数学公式进行数据装配
  return {
    detections: response.detections.map(mapDetectionItem)
  }
}

/**
 * 获取实时摄像头流地址的接口
 */
export async function getCameraStream(): Promise<string> {
  return api.get<string>({ url: '/api/growth/camera/stream' })
}
