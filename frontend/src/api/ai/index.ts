import request from '@/utils/http'
import type {
  AIBootstrapPayload,
  AIContextRequest,
  AIContextSummary,
  AIInvokeResponse,
  AISuggestionResponse,
  AIConfirmPreview,
} from '@/types'

export function fetchAIBootstrap(payload: AIContextRequest) {
  return request.post<AIBootstrapPayload>({
    url: '/api/ai/agent/bootstrap',
    data: payload,
  })
}

export function fetchAIContext(payload: AIContextRequest) {
  return request.post<AIContextSummary>({
    url: '/api/ai/agent/context',
    data: payload,
  })
}

export function fetchAIInvoke(payload: {
  pageId: AIContextRequest['pageId']
  messages: Array<{ role: 'system' | 'user' | 'assistant' | 'tool'; content: string }>
  contextVersion: string
  pageContextSummary: Record<string, unknown>
  allowedTools: string[]
}) {
  return request.post<AIInvokeResponse>({
    url: '/api/ai/agent/invoke',
    data: payload,
  })
}

export function fetchFeedingSuggestions(payload: AIContextRequest) {
  return request.post<AISuggestionResponse>({
    url: '/api/ai/suggestions/feeding',
    data: payload,
  })
}

export function fetchManualFeedingPreview(payload: { pondId?: string; amount: number }) {
  return request.post<AIConfirmPreview>({
    url: '/api/ai/actions/manual-feeding/preview',
    data: payload,
  })
}
