<template>
  <ElDialog
    v-model="visible"
    width="720px"
    class="ai-assistant-dialog"
    append-to-body
    destroy-on-close
    @closed="handleClosed"
  >
    <template #header>
      <div class="dialog-title">
        <ArtSvgIcon icon="ri:deepseek-fill" class="dialog-title-icon" />
        <span>AI 助手</span>
      </div>
    </template>

    <div class="assistant-shell">
      <header class="assistant-header">
        <div class="context-main">
          <span class="context-badge">{{ currentPageLabel }}</span>
          <span class="mode-badge" :class="environmentMode">{{ modeLabel }}</span>
        </div>
        <div class="context-sub">
          <span v-if="currentContext">上下文版本 {{ currentContext.contextVersion }}</span>
          <span v-if="currentContext">更新时间 {{ formatDateTime(currentContext.updatedAt) }}</span>
        </div>
      </header>

      <ElTabs v-model="activeTab" class="assistant-tabs">
        <ElTabPane label="问答" name="chat">
          <div class="messages-panel">
            <article
              v-for="message in qaMessages"
              :key="message.id"
              class="message-card"
              :class="message.role"
            >
              <header class="message-head">
                <span>{{ message.role === 'user' ? '你' : 'AI 助手' }}</span>
                <time>{{ formatTime(message.createdAt) }}</time>
              </header>
              <div
                v-if="message.role === 'assistant'"
                class="message-content markdown-body"
                v-html="renderMarkdown(message.content)"
              />
              <p v-else class="message-content">{{ message.content }}</p>
            </article>
          </div>
        </ElTabPane>

        <ElTabPane v-if="showAutomationTab" label="自动化" name="automation">
          <div class="automation-panel">
            <section class="preset-grid">
              <button
                v-for="preset in automationPresets"
                :key="preset.key"
                type="button"
                class="preset-card"
                @click="runAutomationPreset(preset)"
              >
                <span class="preset-title">{{ preset.title }}</span>
                <span class="preset-desc">{{ preset.prompt }}</span>
              </button>
            </section>

            <section v-if="automationMessages.length" class="messages-panel automation-messages">
              <article
                v-for="message in automationMessages"
                :key="message.id"
                class="message-card"
                :class="message.role"
              >
                <header class="message-head">
                  <span>{{ message.role === 'user' ? '你' : 'AI 助手' }}</span>
                  <time>{{ formatTime(message.createdAt) }}</time>
                </header>
                <div
                  v-if="message.role === 'assistant'"
                  class="message-content markdown-body"
                  v-html="renderMarkdown(message.content)"
                />
                <p v-else class="message-content">{{ message.content }}</p>
              </article>
            </section>

            <section v-if="latestPreview" class="latest-preview">
              <div class="preview-head">
                <span>操作预览</span>
                <ElTag :type="getRiskType(latestPreview.riskLevel)" size="small">
                  {{ getRiskLabel(latestPreview.riskLevel) }}
                </ElTag>
              </div>
              <p>{{ latestPreview.previewText }}</p>
              <div class="preview-meta">
                <span>确认令牌 {{ latestPreview.confirmToken }}</span>
                <span>失效时间 {{ formatDateTime(latestPreview.expiresAt) }}</span>
              </div>
              <div class="preview-actions">
                <ElButton
                  type="primary"
                  :disabled="!canExecute"
                  :loading="uiState === 'executing'"
                  @click="executeLatestPreview()"
                >
                  确认执行
                </ElButton>
                <ElButton
                  text
                  type="primary"
                  :disabled="!canPreview"
                  @click="requestManualFeedingPreview(600)"
                >
                  重新预览
                </ElButton>
              </div>
            </section>
          </div>
        </ElTabPane>
      </ElTabs>

      <footer class="assistant-input">
        <ElInput
          v-model="draft"
          type="textarea"
          :rows="3"
          resize="none"
          :disabled="loading"
          placeholder="请输入你的问题或自动化需求"
          @keydown.ctrl.enter.prevent="submitDraft()"
        />
        <div class="input-actions">
          <span class="hint">Ctrl + Enter 发送</span>
          <ElButton
            type="primary"
            :loading="loading"
            :disabled="!draft.trim()"
            @click="submitDraft()"
          >
            发送
          </ElButton>
        </div>
      </footer>
    </div>
  </ElDialog>
</template>

<script setup lang="ts">
  import { storeToRefs } from 'pinia'
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import { AI_PAGE_LABEL } from '@/config/ai'
  import { useAIStore } from '@/store/modules/ai'
  import { renderMarkdown } from '@/utils/markdown'
  import type { AIAutomationPreset, AIRiskLevel } from '@/types'

  defineOptions({ name: 'ArtAIAssistant' })

  const aiStore = useAIStore()
  const {
    visible,
    loading,
    draft,
    activeTab,
    currentContext,
    bootstrap,
    messages,
    latestPreview,
    automationPresets,
    automationMessages,
    qaMessages,
    canExecute,
    canPreview,
    showAutomationTab,
    modeLabel,
    uiState
  } = storeToRefs(aiStore)

  const environmentMode = computed(() => bootstrap.value?.environmentMode ?? 'mock')

  const currentPageLabel = computed(() => {
    const currentPageId = currentContext.value?.currentPage.pageId ?? 'global-chat'
    return AI_PAGE_LABEL[currentPageId]
  })

  const formatTime = (value: string) => {
    const date = new Date(value)
    return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
  }

  const formatDateTime = (value: string) => {
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) return value
    return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date
      .getDate()
      .toString()
      .padStart(2, '0')} ${formatTime(value)}`
  }

  const getRiskType = (level: AIRiskLevel) => {
    if (level === 'critical') return 'danger'
    if (level === 'warning') return 'warning'
    return 'success'
  }

  const getRiskLabel = (level: AIRiskLevel) => {
    if (level === 'critical') return '高风险'
    if (level === 'warning') return '中风险'
    return '低风险'
  }

  const runAutomationPreset = async (preset: AIAutomationPreset) => {
    await aiStore.runAutomationPreset(preset)
  }

  const requestManualFeedingPreview = async (amount: number) => {
    await aiStore.requestManualFeedingPreview(amount)
  }

  const executeLatestPreview = async () => {
    await aiStore.executeLatestPreview()
  }

  const submitDraft = async () => {
    await aiStore.submitDraft()
  }

  const handleClosed = () => {
    aiStore.closeAssistant()
  }
</script>

<style scoped lang="scss">
  .dialog-title {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-size: 18px;
    font-weight: 600;
    color: var(--el-text-color-primary);
  }

  .dialog-title-icon {
    font-size: 18px;
    line-height: 1;
    color: var(--el-text-color-primary);
  }

  .assistant-shell {
    display: flex;
    height: 600px;
    flex-direction: column;
    gap: 14px;
    overflow: hidden;
  }

  .assistant-header {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    padding: 10px 12px;
    border: 1px solid var(--art-card-border);
    border-radius: 12px;
    background: var(--default-box-color);
  }

  .context-main,
  .context-sub,
  .input-actions,
  .preview-head,
  .preview-meta,
  .message-head {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .context-sub {
    font-size: 12px;
    color: var(--el-text-color-secondary);
  }

  .context-badge,
  .mode-badge {
    display: inline-flex;
    align-items: center;
    padding: 4px 10px;
    font-size: 12px;
    font-weight: 700;
    border-radius: 999px;
  }

  .context-badge {
    color: var(--el-color-primary);
    background: color-mix(in srgb, var(--el-color-primary) 10%, transparent);
  }

  .mode-badge {
    color: #92400e;
    background: #fef3c7;
  }

  .mode-badge.real {
    color: #166534;
    background: #dcfce7;
  }

  .assistant-tabs {
    flex: 1;
    min-height: 0;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }

  :deep(.el-tabs__content) {
    flex: 1;
    min-height: 0;
    overflow: hidden;
  }

  :deep(.el-tab-pane) {
    height: 100%;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }

  .messages-panel,
  .automation-panel {
    display: flex;
    flex: 1;
    min-height: 0;
    flex-direction: column;
    gap: 12px;
  }

  .messages-panel {
    overflow-y: auto;
    padding-right: 6px;
  }

  .message-card {
    padding: 14px;
    border: 1px solid var(--art-card-border);
    border-radius: 14px;
    background: var(--default-box-color);
  }

  .message-card.user {
    border-color: color-mix(in srgb, var(--el-color-primary) 25%, var(--art-card-border));
  }

  .message-head {
    justify-content: space-between;
    font-size: 12px;
    color: var(--el-text-color-secondary);
  }

  .message-content {
    margin: 8px 0 0;
    white-space: pre-wrap;
    line-height: 1.65;
  }

  .preset-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 10px;
  }

  .preset-card {
    display: flex;
    min-height: 116px;
    flex-direction: column;
    gap: 8px;
    padding: 14px;
    text-align: left;
    cursor: pointer;
    border: 1px solid var(--art-card-border);
    border-radius: 14px;
    background: var(--default-box-color);
    transition:
      transform 0.18s ease,
      box-shadow 0.18s ease,
      border-color 0.18s ease;
  }

  .preset-card:hover {
    transform: translateY(-1px);
    border-color: color-mix(in srgb, var(--el-color-primary) 30%, var(--art-card-border));
    box-shadow: 0 8px 22px rgb(15 23 42 / 8%);
  }

  .preset-title {
    color: var(--el-text-color-primary);
    font-weight: 700;
  }

  .preset-desc {
    font-size: 13px;
    line-height: 1.5;
    color: var(--el-text-color-secondary);
  }

  .latest-preview {
    display: flex;
    flex-direction: column;
    gap: 10px;
    padding: 12px;
    border: 1px solid color-mix(in srgb, var(--el-color-warning) 20%, transparent);
    border-radius: 12px;
    background: color-mix(in srgb, var(--el-color-warning) 9%, var(--default-box-color));
  }

  .preview-meta {
    flex-wrap: wrap;
    font-size: 12px;
    color: var(--el-text-color-secondary);
  }

  .preview-actions {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .assistant-input {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .input-actions {
    justify-content: space-between;
  }

  .hint {
    font-size: 12px;
    color: var(--el-text-color-secondary);
  }

  @media (width <= 900px) {
    .assistant-header,
    .context-sub,
    .input-actions {
      flex-direction: column;
      align-items: flex-start;
    }

    .preset-grid {
      grid-template-columns: 1fr;
    }
  }

  :global(.dark) .assistant-header,
  :global(.dark) .message-card,
  :global(.dark) .preset-card {
    border-color: color-mix(in oklch, var(--el-color-primary) 18%, var(--art-card-border));
    background: var(--art-nested-card-bg);
  }

  :global(.dark) .message-card.user {
    border-color: color-mix(in oklch, var(--el-color-primary) 36%, var(--art-card-border));
    box-shadow: inset 0 1px 0 color-mix(in oklch, var(--el-color-primary) 12%, transparent);
  }

  :global(.dark) .preset-card:hover {
    background: var(--art-nested-card-hover);
    box-shadow:
      0 10px 22px rgb(0 0 0 / 34%),
      0 0 0 1px color-mix(in oklch, var(--el-color-primary) 25%, transparent);
  }

  :global(.dark) .latest-preview {
    border-color: color-mix(in oklch, var(--el-color-warning) 32%, transparent);
    background: color-mix(in oklch, var(--el-color-warning) 14%, var(--art-nested-card-bg));
  }
</style>
