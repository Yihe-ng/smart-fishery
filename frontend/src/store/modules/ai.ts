import { ElMessage } from 'element-plus'
import { defineStore } from 'pinia'

import {
  executeManualFeeding,
  fetchAIBootstrap,
  fetchAIContext,
  fetchAIInvoke,
  fetchManualFeedingPreview
} from '@/api/ai'
import { AI_MODE_LABEL, AI_WARNING_BLACKLIST, AI_WELCOME_MESSAGE } from '@/config/ai'
import type {
  AIAutomationPreset,
  AIBootstrapPayload,
  AIChatMessage,
  AIConfirmPreview,
  AIContextRequest,
  AIContextSummary,
  AIIntentType,
  AIPageId,
  AIRiskLevel,
  AITabKey,
  AIUIState
} from '@/types'

const AUTOMATION_PRESETS: AIAutomationPreset[] = [
  {
    key: 'manual-feeding-preview',
    title: '生成手动投喂预览',
    prompt: '请基于当前页面状态，生成 600g 手动投喂预览，并说明风险。'
  },
  {
    key: 'feeding-advice',
    title: '投喂建议分析',
    prompt: '请根据当前监测数据给出投喂建议，并说明原因。'
  },
  {
    key: 'alert-summary',
    title: '告警快速摘要',
    prompt: '请总结当前页面关键告警，并给出优先处理顺序。'
  }
]

function createMessage(
  role: AIChatMessage['role'],
  content: string,
  overrides: Partial<AIChatMessage> = {}
): AIChatMessage {
  return {
    id: `${role}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    role,
    content,
    createdAt: new Date().toISOString(),
    ...overrides
  }
}

function sanitizeWarnings(warnings: string[] = []): string[] {
  return warnings.filter(
    (warning) =>
      warning &&
      !AI_WARNING_BLACKLIST.some((keyword) => warning.toLowerCase().includes(keyword.toLowerCase()))
  )
}

function getConfirmThreshold(level: AIRiskLevel): number {
  if (level === 'critical') return 2
  if (level === 'warning') return 1
  return 0
}

export const useAIStore = defineStore('aiStore', () => {
  const visible = ref(false)
  const loading = ref(false)
  const draft = ref('')
  const activeTab = ref<AITabKey>('chat')
  const uiState = ref<AIUIState>('idle')
  const intentType = ref<AIIntentType>('qa')

  const bootstrap = ref<AIBootstrapPayload | null>(null)
  const currentContext = ref<AIContextSummary | null>(null)
  const pageId = ref<AIPageId>('global-chat')
  const routePath = ref('/')
  const pondId = ref<string>()

  const messages = ref<AIChatMessage[]>([])
  const latestPreview = ref<AIConfirmPreview | null>(null)
  const pendingConfirmToken = ref<string | null>(null)
  const confirmStep = ref(0)
  const automationPresets = ref<AIAutomationPreset[]>(AUTOMATION_PRESETS)

  const canExecute = computed(() => bootstrap.value?.uiCapabilities.canExecute ?? false)
  const canPreview = computed(() => bootstrap.value?.uiCapabilities.canPreview ?? true)
  const showAutomationTab = computed(
    () => bootstrap.value?.uiCapabilities.showAutomationTab ?? true
  )

  const resetExecutionState = () => {
    latestPreview.value = null
    pendingConfirmToken.value = null
    confirmStep.value = 0
  }

  const resetConversationState = () => {
    uiState.value = 'idle'
    intentType.value = 'qa'
    loading.value = false
    draft.value = ''
    resetExecutionState()
  }

  const buildInvokeMessages = (
    text: string
  ): Array<{ role: 'system' | 'user' | 'assistant' | 'tool'; content: string }> => {
    const history = messages.value
      .slice(-8)
      .map((message) => ({
        role: (message.role === 'user' ? 'user' : 'assistant') as 'user' | 'assistant',
        content: message.content
      }))
      .filter((message) => message.content.trim().length > 0)

    return [...history, { role: 'user' as const, content: text }]
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
  }

  const appendAssistantMessage = (content: string, overrides: Partial<AIChatMessage> = {}) => {
    messages.value.push(createMessage('assistant', content, overrides))
  }

  const invokeAssistant = async (text: string, currentIntent: AIIntentType) => {
    if (!bootstrap.value || !currentContext.value) {
      throw new Error('AI 上下文未准备完成')
    }

    const response = await fetchAIInvoke({
      pageId: pageId.value,
      messages: buildInvokeMessages(text),
      contextVersion: currentContext.value.contextVersion,
      pageContextSummary: currentContext.value as unknown as Record<string, unknown>,
      allowedTools: bootstrap.value.allowedTools
    })

    const warnings = sanitizeWarnings(response.warnings)
    const messageText = response.assistantMessage?.trim() || '当前暂无可返回结果。'
    const preview = currentIntent === 'automation' ? (response.confirmPreview ?? null) : null

    if (preview) {
      latestPreview.value = preview
      pendingConfirmToken.value = preview.confirmToken
      confirmStep.value = 0
      uiState.value = 'previewing'
    } else {
      resetExecutionState()
      uiState.value = 'idle'
    }

    appendAssistantMessage(messageText, {
      warnings,
      confirmPreview: preview
    })
  }

  const openAssistant = async (
    payload: AIContextRequest,
    options?: { activeTab?: AITabKey; initialPrompt?: string }
  ) => {
    visible.value = true
    activeTab.value = options?.activeTab ?? 'chat'

    const shouldRebootstrap =
      !bootstrap.value ||
      pageId.value !== payload.pageId ||
      routePath.value !== payload.routePath ||
      pondId.value !== payload.pondId

    if (shouldRebootstrap) {
      await bootstrapSession(payload)
      messages.value = [createMessage('assistant', AI_WELCOME_MESSAGE)]
      resetConversationState()
    } else {
      await syncContext(payload)
    }

    if (options?.initialPrompt) {
      draft.value = options.initialPrompt
      if (activeTab.value === 'automation') {
        await runAutomation(options.initialPrompt)
      } else {
        await sendQA(options.initialPrompt)
      }
    }
  }

  const closeAssistant = () => {
    visible.value = false
    resetConversationState()
  }

  const sendQA = async (input?: string) => {
    const text = (input ?? draft.value).trim()
    if (!text || loading.value) return

    intentType.value = 'qa'
    uiState.value = 'chatting'
    loading.value = true
    draft.value = ''
    messages.value.push(createMessage('user', text))
    resetExecutionState()

    try {
      await invokeAssistant(text, 'qa')
    } catch (error) {
      uiState.value = 'failed'
      appendAssistantMessage(
        `当前请求失败：${error instanceof Error ? error.message : '未知错误，请稍后重试。'}`
      )
    } finally {
      loading.value = false
      if (uiState.value === 'chatting') {
        uiState.value = 'idle'
      }
    }
  }

  const runAutomation = async (input: string) => {
    const text = input.trim()
    if (!text || loading.value) return

    intentType.value = 'automation'
    uiState.value = 'chatting'
    loading.value = true
    draft.value = ''
    messages.value.push(createMessage('user', text))

    try {
      await invokeAssistant(text, 'automation')
    } catch (error) {
      uiState.value = 'failed'
      appendAssistantMessage(
        `自动化请求失败：${error instanceof Error ? error.message : '未知错误，请稍后重试。'}`
      )
    } finally {
      loading.value = false
      if (uiState.value === 'chatting') {
        uiState.value = 'idle'
      }
    }
  }

  const runAutomationPreset = async (preset: AIAutomationPreset) => {
    activeTab.value = 'automation'
    await runAutomation(preset.prompt)
  }

  const requestManualFeedingPreview = async (amount: number) => {
    if (!canPreview.value || loading.value) return

    intentType.value = 'automation'
    uiState.value = 'previewing'
    loading.value = true
    try {
      const preview = await fetchManualFeedingPreview({ pondId: pondId.value, amount })
      latestPreview.value = preview
      pendingConfirmToken.value = preview.confirmToken
      confirmStep.value = 0
      appendAssistantMessage(preview.previewText, {
        confirmPreview: preview
      })
    } catch (error) {
      uiState.value = 'failed'
      appendAssistantMessage(
        `预览生成失败：${error instanceof Error ? error.message : '未知错误，请稍后重试。'}`
      )
    } finally {
      loading.value = false
    }
  }

  const executeLatestPreview = async () => {
    if (!latestPreview.value || !canExecute.value || loading.value) return

    const preview = latestPreview.value
    const required = getConfirmThreshold(preview.riskLevel)
    if (confirmStep.value < required) {
      confirmStep.value += 1
      uiState.value = 'confirming'

      if (preview.riskLevel === 'critical' && confirmStep.value < required) {
        appendAssistantMessage('当前操作为高风险，请再次确认后执行。')
      } else {
        appendAssistantMessage('请确认执行该操作。再次点击“确认执行”即可继续。')
      }
      return
    }

    uiState.value = 'executing'
    loading.value = true
    try {
      await executeManualFeeding({
        feederId: 'feeder-001',
        amount: Number(preview.previewText.match(/(\d+)\s*g/i)?.[1] ?? 600),
        duration: 10
      })
      appendAssistantMessage('操作已下发：手动投喂执行成功。')
      resetExecutionState()
      uiState.value = 'idle'
      ElMessage.success('自动化操作执行成功')
    } catch (error) {
      uiState.value = 'failed'
      appendAssistantMessage(
        `执行失败：${error instanceof Error ? error.message : '未知错误，请稍后重试。'}`
      )
    } finally {
      loading.value = false
    }
  }

  const submitDraft = async () => {
    if (activeTab.value === 'automation') {
      await runAutomation(draft.value)
      return
    }
    await sendQA(draft.value)
  }

  const modeLabel = computed(() => {
    const mode = bootstrap.value?.environmentMode ?? 'mock'
    return AI_MODE_LABEL[mode]
  })

  return {
    visible,
    loading,
    draft,
    activeTab,
    uiState,
    intentType,
    bootstrap,
    currentContext,
    pageId,
    routePath,
    pondId,
    messages,
    latestPreview,
    automationPresets,
    canExecute,
    canPreview,
    showAutomationTab,
    modeLabel,
    openAssistant,
    closeAssistant,
    sendQA,
    runAutomation,
    runAutomationPreset,
    requestManualFeedingPreview,
    executeLatestPreview,
    submitDraft
  }
})
