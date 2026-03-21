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
}) {
  return request.post<AIAgentInvokeResponse>({
    url: '/api/agent/agent/invoke',
    data: payload
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
  feederId: string
  amount: number
  duration?: number
}) {
  return request.post<{ success: boolean; message?: string }>({
    url: '/api/feeding/execute',
    params: {
      feeder_id: payload.feederId,
      amount: payload.amount,
      duration: payload.duration ?? 10
    }
  })
}
