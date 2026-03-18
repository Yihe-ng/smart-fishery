import { defineStore } from 'pinia'

import { fetchAIBootstrap, fetchAIContext, fetchManualFeedingPreview } from '@/api/ai'
import { consumeLastInvokeResponse, createPageAgent, createPreviewMessage } from '@/ai/page-agent-runtime'
import type {
  AIAutomationPreset,
  AIBootstrapPayload,
  AIChatMessage,
  AIConfirmPreview,
  AIContextRequest,
  AIContextSummary,
  AIPageId,
  AITabKey,
} from '@/types'

let agentInstance: { execute: (task: string) => Promise<{ data: string }>; dispose: () => void } | null = null

const AUTOMATION_PRESETS: AIAutomationPreset[] = [
  {
    key: 'feeding-recommendation',
    title: '投喂建议',
    prompt: '请基于当前页面上下文，给出当前鱼塘的投喂建议和原因。',
  },
  {
    key: 'page-alert-summary',
    title: '告警摘要',
    prompt: '请总结当前页面的主要风险、告警和设备状态。',
  },
  {
    key: 'operation-plan',
    title: '操作建议',
    prompt: '请结合当前页面数据，给出下一步运维建议。',
  },
]

function createMessage(
  role: AIChatMessage['role'],
  content: string,
  overrides: Partial<AIChatMessage> = {},
): AIChatMessage {
  return {
    id: `${role}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    role,
    content,
    createdAt: new Date().toISOString(),
    ...overrides,
  }
}

function createBootstrapNotice(environmentMode: 'mock' | 'real') {
  if (environmentMode === 'real') {
    return '已接入当前页面 AI 上下文，当前处于 real 模式，我会结合页面数据直接回答你的问题。'
  }

  return '已接入当前页面 AI 上下文，当前仍处于 mock 模式，所有建议和预览都不会触发真实执行。'
}

export const useAIStore = defineStore('aiStore', () => {
  const visible = ref(false)
  const loading = ref(false)
  const draft = ref('')
  const activeTab = ref<AITabKey>('chat')
  const bootstrap = ref<AIBootstrapPayload | null>(null)
  const currentContext = ref<AIContextSummary | null>(null)
  const pageId = ref<AIPageId>('global-chat')
  const routePath = ref('/')
  const pondId = ref<string>()
  const messages = ref<AIChatMessage[]>([])
  const latestPreview = ref<AIConfirmPreview | null>(null)
  const automationPresets = ref<AIAutomationPreset[]>(AUTOMATION_PRESETS)

  const disposeAgent = () => {
    if (agentInstance) {
      agentInstance.dispose()
      agentInstance = null
    }
  }

  const ensureAgent = async () => {
    if (!bootstrap.value) {
      throw new Error('AI bootstrap not ready')
    }

    disposeAgent()
    agentInstance = await createPageAgent({
      pageId: pageId.value,
      bootstrap: bootstrap.value,
    })
  }

  const syncContext = async (payload: AIContextRequest) => {
    currentContext.value = await fetchAIContext(payload)
    if (bootstrap.value) {
      bootstrap.value.pageContextSummary = currentContext.value
    }
  }

  const bootstrapSession = async (payload: AIContextRequest) => {
    pageId.value = payload.pageId
    routePath.value = payload.routePath
    pondId.value = payload.pondId
    bootstrap.value = await fetchAIBootstrap(payload)
    currentContext.value = bootstrap.value.pageContextSummary
    await ensureAgent()
  }

  const openAssistant = async (
    payload: AIContextRequest,
    options?: { activeTab?: AITabKey; initialPrompt?: string },
  ) => {
    visible.value = true
    activeTab.value = options?.activeTab ?? 'chat'

    const shouldRebootstrap =
      !bootstrap.value ||
      pageId.value !== payload.pageId ||
      routePath.value !== payload.routePath ||
      pondId.value !== payload.pondId

    if (shouldRebootstrap) {
      latestPreview.value = null
      await bootstrapSession(payload)
      if (bootstrap.value) {
        messages.value = [createMessage('assistant', createBootstrapNotice(bootstrap.value.environmentMode))]
      }
    } else {
      await syncContext(payload)
    }

    if (options?.initialPrompt) {
      draft.value = options.initialPrompt
      await sendMessage(options.initialPrompt)
    }
  }

  const closeAssistant = () => {
    visible.value = false
    loading.value = false
    draft.value = ''
    latestPreview.value = null
    disposeAgent()
  }

  const sendMessage = async (input?: string) => {
    const text = (input ?? draft.value).trim()
    if (!text || loading.value) {
      return
    }

    loading.value = true
    draft.value = ''
    messages.value.push(createMessage('user', text))

    try {
      if (!agentInstance) {
        await ensureAgent()
      }

      const result = await agentInstance!.execute(text)
      const invokeResponse = consumeLastInvokeResponse()
      latestPreview.value = invokeResponse?.confirmPreview ?? null
      const assistantText = invokeResponse?.assistantMessage?.trim() || result.data

      messages.value.push(
        createMessage('assistant', assistantText, {
          warnings: invokeResponse?.warnings ?? [],
          confirmPreview: invokeResponse?.confirmPreview ?? null,
        }),
      )
    } catch (error) {
      messages.value.push(
        createMessage(
          'assistant',
          `AI 调用失败：${error instanceof Error ? error.message : '未知错误'}`,
        ),
      )
    } finally {
      loading.value = false
    }
  }

  const runAutomationPreset = async (preset: AIAutomationPreset) => {
    activeTab.value = 'automation'
    await sendMessage(preset.prompt)
  }

  const requestManualFeedingPreview = async (amount: number) => {
    const preview = await fetchManualFeedingPreview({ pondId: pondId.value, amount })
    latestPreview.value = preview
    messages.value.push(
      createMessage('assistant', createPreviewMessage(preview), {
        confirmPreview: preview,
        warnings: ['当前返回的是预览结果，不会直接触发真实投喂。'],
      }),
    )
  }

  return {
    visible,
    loading,
    draft,
    activeTab,
    bootstrap,
    currentContext,
    pageId,
    routePath,
    pondId,
    messages,
    latestPreview,
    automationPresets,
    openAssistant,
    closeAssistant,
    sendMessage,
    runAutomationPreset,
    requestManualFeedingPreview,
  }
})
