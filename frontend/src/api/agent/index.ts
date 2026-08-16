import request from '@/utils/http'
import type {
  AIAgentInvokeResponse,
  AIBootstrapPayload,
  AIConfirmPreview,
  AIContextRequest,
  AIContextSummary,
  AISuggestionResponse,
  AIToolExecuteRequest,
  AIToolExecuteResponse
} from '@/types'

export function fetchAIBootstrap(payload: AIContextRequest) {
  return request.post<AIBootstrapPayload>({
    url: '/api/agent/agent/bootstrap',
    data: payload
  })
}

export function fetchAIContext(payload: AIContextRequest) {
  return request.post<AIContextSummary>({
    url: '/api/agent/agent/context',
    data: payload
  })
}

export function fetchAIInvoke(payload: {
  pageId: AIContextRequest['pageId']
  messages: Array<{ role: 'system' | 'user' | 'assistant' | 'tool'; content: string }>
  contextVersion: string
  pageContextSummary: Record<string, unknown>
  allowedTools: string[]
  currentIndex?: number
}) {
  return request.post<AIAgentInvokeResponse>({
    url: '/api/agent/agent/invoke',
    data: payload,
    // 真实 LLM 最多 3 轮决策（每轮 20s 超时）+ 工具执行，默认 15s 会在模型慢时被前端掐断，
    // 出现"网络连接异常"但后端日志仍为 200 的假象；放宽到 90s 与图片识别一致。
    timeout: 90_000
  })
}

export function fetchExecuteTool(toolName: string, payload: AIToolExecuteRequest) {
  return request.post<AIToolExecuteResponse>({
    url: `/api/agent/tools/${toolName}`,
    data: payload
  })
}

export function fetchFeedingSuggestions(payload: AIContextRequest) {
  return request.post<AISuggestionResponse>({
    url: '/api/agent/suggestions/feeding',
    data: payload
  })
}

export function fetchManualFeedingPreview(payload: { pondId?: string; amount: number }) {
  return request.post<AIConfirmPreview>({
    url: '/api/agent/actions/manual-feeding/preview',
    data: payload
  })
}

export function executeManualFeeding(payload: {
  confirmToken: string
  feederId: string
  amount: number
  pondId?: string
  duration?: number
}) {
  return request.post<{ success: boolean; message?: string }>({
    url: '/api/feeding/execute',
    data: {
      confirmToken: payload.confirmToken,
      feederId: payload.feederId,
      amount: payload.amount,
      pondId: payload.pondId,
      duration: payload.duration ?? 10
    }
  })
}
