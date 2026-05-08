import { PageAgentCore } from 'page-agent'
import { PageController } from '@page-agent/page-controller'

import { fetchAIInvoke } from '@/api/agent'
import { createProxyTools } from '@/agent/proxy-tools'
import type {
  AIAgentInvokeResponse,
  AIBootstrapPayload,
  AIConfirmPreview,
  AIPageId
} from '@/types'

interface AgentRuntimeContext {
  pageId: AIPageId
  bootstrap: AIBootstrapPayload
  intent: 'qa' | 'automation'
}

export interface QAResult {
  data: AIAgentInvokeResponse
  success: boolean
}

export async function runQA(context: AgentRuntimeContext, text: string): Promise<QAResult> {
  const allowedTools =
    context.intent === 'automation'
      ? context.bootstrap.allowedTools
      : context.bootstrap.allowedTools.filter((t) => t !== 'preview_manual_feeding_action')

  const response = await fetchAIInvoke({
    pageId: context.pageId,
    messages: [{ role: 'user', content: text }],
    contextVersion: context.bootstrap.pageContextSummary.contextVersion,
    pageContextSummary: context.bootstrap.pageContextSummary as unknown as Record<string, unknown>,
    allowedTools
  })

  return {
    data: response,
    success: response.status !== 'degraded' && response.status !== 'failed'
  }
}

export async function createPageAgent(context: AgentRuntimeContext) {
  const customFetch: typeof fetch = async (_input, init) => {
    const body = init?.body ? JSON.parse(String(init.body)) : {}
    const messages = (body.messages ?? []).map((m: { role: string; content: unknown }) => ({
      role: m.role,
      content: String(m.content ?? '')
    }))

    const response = await fetchAIInvoke({
      pageId: context.pageId,
      messages,
      contextVersion: context.bootstrap.pageContextSummary.contextVersion,
      pageContextSummary: context.bootstrap.pageContextSummary as unknown as Record<
        string,
        unknown
      >,
      allowedTools: context.bootstrap.allowedTools
    })

    return new Response(JSON.stringify(response), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    })
  }

  return new PageAgentCore({
    baseURL: '/api/agent/agent/invoke',
    apiKey: 'server-proxied',
    model: 'smart-fish-page-agent-proxy',
    customFetch,
    pageController: new PageController({ enableMask: false }),
    language: 'zh-CN',
    stepDelay: 300,
    customTools: {
      execute_javascript: null,
      ...createProxyTools(context.bootstrap.allowedTools)
    },
    instructions: {
      system: context.bootstrap.systemInstructions,
      getPageInstructions: () => context.bootstrap.pageInstructions
    }
  })
}

export function createPreviewMessage(preview: AIConfirmPreview): string {
  return `${preview.previewText}\n\n风险等级：${preview.riskLevel}\n确认令牌：${preview.confirmToken}`
}
