<template>
  <ElDialog
    v-model="visible"
    title="AI 助手"
    width="720px"
    class="ai-assistant-dialog"
    append-to-body
    destroy-on-close
    @closed="handleClosed"
  >
    <div class="assistant-shell">
      <div class="assistant-header">
        <div class="context-meta">
          <span class="context-badge">{{ currentPageLabel }}</span>
          <span class="mode-badge" :class="environmentMode">{{ environmentMode.toUpperCase() }}</span>
        </div>
        <div class="context-summary">
          <span v-if="currentContext">上下文版本 {{ currentContext.contextVersion }}</span>
          <span v-if="currentContext">更新时间 {{ currentContext.updatedAt }}</span>
        </div>
      </div>

      <ElTabs v-model="activeTab" class="assistant-tabs">
        <ElTabPane label="问答" name="chat">
          <div class="messages-panel">
            <div v-if="messages.length === 0" class="empty-state">
              <ArtSvgIcon icon="ri:robot-2-line" size="28" />
              <p>当前会话为空，可以直接询问水质、投喂建议或页面异常。</p>
            </div>

            <article
              v-for="message in messages"
              :key="message.id"
              class="message-card"
              :class="message.role"
            >
              <header class="message-head">
                <span>{{ message.role === 'user' ? '你' : 'AI 助手' }}</span>
                <time>{{ formatTime(message.createdAt) }}</time>
              </header>
              <p class="message-content">{{ message.content }}</p>

              <div v-if="message.warnings?.length" class="message-warnings">
                <span v-for="warning in message.warnings" :key="warning">{{ warning }}</span>
              </div>

              <div v-if="message.confirmPreview" class="preview-card">
                <div class="preview-head">
                  <span>操作预览</span>
                  <ElTag :type="getSeverityType(message.confirmPreview.riskLevel)" size="small">
                    {{ message.confirmPreview.riskLevel }}
                  </ElTag>
                </div>
                <p>{{ message.confirmPreview.previewText }}</p>
                <div class="preview-meta">
                  <span>令牌：{{ message.confirmPreview.confirmToken }}</span>
                  <span>失效：{{ message.confirmPreview.expiresAt }}</span>
                </div>
              </div>
            </article>
          </div>
        </ElTabPane>

        <ElTabPane label="自动化" name="automation">
          <div class="automation-panel">
            <div class="preset-grid">
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
            </div>

            <div class="latest-preview" v-if="latestPreview">
              <div class="preview-head">
                <span>最近操作预览</span>
                <ElButton link type="primary" @click="requestManualFeedingPreview(600)">
                  重新生成 600g 预览
                </ElButton>
              </div>
              <p>{{ latestPreview.previewText }}</p>
              <div class="preview-meta">
                <span>风险：{{ latestPreview.riskLevel }}</span>
                <span>模式：{{ latestPreview.mode }}</span>
              </div>
            </div>
          </div>
        </ElTabPane>
      </ElTabs>

      <div class="assistant-input">
        <ElInput
          v-model="draft"
          type="textarea"
          :rows="3"
          resize="none"
          placeholder="输入你的问题或自动化需求"
          @keydown.ctrl.enter.prevent="sendMessage()"
        />
        <div class="input-actions">
          <span class="hint">Ctrl + Enter 发送</span>
          <ElButton type="primary" :loading="loading" @click="sendMessage()">发送</ElButton>
        </div>
      </div>
    </div>
  </ElDialog>
</template>

<script setup lang="ts">
  import { storeToRefs } from 'pinia'
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import { useAIStore } from '@/store/modules/ai'
  import type { AIAutomationPreset, AISeverity } from '@/types'

  defineOptions({ name: 'ArtAIAssistant' })

  const aiStore = useAIStore()
  const { visible, loading, draft, activeTab, currentContext, bootstrap, messages, latestPreview, automationPresets } =
    storeToRefs(aiStore)

  const environmentMode = computed(() => bootstrap.value?.environmentMode ?? 'mock')

  const currentPageLabel = computed(() => {
    const pageId = (currentContext.value?.currentPage.pageId ?? 'global-chat') as
      | 'global-chat'
      | 'fishery-dashboard'
      | 'feeding'
      | 'water-quality'
      | 'growth'
    const pageMap = {
      'global-chat': '全局会话',
      'fishery-dashboard': '渔业总览',
      feeding: '精准投喂',
      'water-quality': '水质监测',
      growth: '生长监测',
    } as const

    return pageMap[pageId]
  })

  const formatTime = (value: string) => {
    const date = new Date(value)
    return `${date.getHours().toString().padStart(2, '0')}:${date
      .getMinutes()
      .toString()
      .padStart(2, '0')}`
  }

  const getSeverityType = (severity: AISeverity) => {
    if (severity === 'critical') return 'danger'
    if (severity === 'warning') return 'warning'
    return 'info'
  }

  const sendMessage = async () => {
    await aiStore.sendMessage()
  }

  const runAutomationPreset = async (preset: AIAutomationPreset) => {
    await aiStore.runAutomationPreset(preset)
  }

  const requestManualFeedingPreview = async (amount: number) => {
    await aiStore.requestManualFeedingPreview(amount)
  }

  const handleClosed = () => {
    aiStore.closeAssistant()
  }
</script>

<style scoped lang="scss">
  .assistant-shell {
    display: flex;
    min-height: 560px;
    flex-direction: column;
    gap: 16px;
  }

  .assistant-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 16px;
  }

  .context-meta,
  .context-summary,
  .input-actions,
  .preview-head,
  .preview-meta,
  .message-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }

  .context-badge,
  .mode-badge {
    padding: 4px 10px;
    font-size: 12px;
    font-weight: 700;
    border-radius: 999px;
  }

  .context-badge {
    color: var(--el-color-primary);
    background: color-mix(in srgb, var(--el-color-primary) 12%, transparent);
  }

  .mode-badge {
    color: #92400e;
    background: #fef3c7;
  }

  .context-summary {
    color: var(--el-text-color-secondary);
    font-size: 12px;
  }

  .assistant-tabs {
    flex: 1;
    min-height: 0;
  }

  .messages-panel,
  .automation-panel {
    display: flex;
    min-height: 360px;
    flex-direction: column;
    gap: 12px;
  }

  .messages-panel {
    overflow: auto;
    padding-right: 6px;
  }

  .empty-state {
    display: flex;
    height: 100%;
    min-height: 240px;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
    color: var(--el-text-color-secondary);
    border: 1px dashed var(--art-card-border);
    border-radius: 16px;
  }

  .message-card {
    padding: 14px 16px;
    border: 1px solid var(--art-card-border);
    border-radius: 16px;
    background: var(--default-box-color);

    &.user {
      background: color-mix(in srgb, var(--el-color-primary) 8%, var(--default-box-color));
    }
  }

  .message-head {
    font-size: 12px;
    color: var(--el-text-color-secondary);
  }

  .message-content {
    margin: 8px 0 0;
    white-space: pre-wrap;
    line-height: 1.65;
  }

  .message-warnings {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 10px;

    span {
      padding: 4px 8px;
      font-size: 12px;
      color: #92400e;
      background: #fef3c7;
      border-radius: 999px;
    }
  }

  .preview-card,
  .latest-preview {
    display: flex;
    flex-direction: column;
    gap: 10px;
    padding: 14px;
    margin-top: 12px;
    border-radius: 14px;
    background: color-mix(in srgb, var(--el-color-warning) 10%, var(--default-box-color));
    border: 1px solid color-mix(in srgb, var(--el-color-warning) 24%, transparent);
  }

  .preview-meta {
    flex-wrap: wrap;
    justify-content: flex-start;
    color: var(--el-text-color-secondary);
    font-size: 12px;
  }

  .preset-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
  }

  .preset-card {
    display: flex;
    min-height: 126px;
    flex-direction: column;
    gap: 8px;
    padding: 16px;
    text-align: left;
    cursor: pointer;
    background: linear-gradient(160deg, rgb(14 165 233 / 8%), rgb(34 197 94 / 4%));
    border: 1px solid var(--art-card-border);
    border-radius: 18px;
    transition:
      transform 0.2s ease,
      box-shadow 0.2s ease;

    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 12px 28px rgb(15 23 42 / 10%);
    }
  }

  .preset-title {
    font-weight: 700;
    color: var(--el-text-color-primary);
  }

  .preset-desc {
    font-size: 13px;
    line-height: 1.6;
    color: var(--el-text-color-secondary);
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
    .context-summary,
    .input-actions {
      flex-direction: column;
      align-items: flex-start;
    }

    .preset-grid {
      grid-template-columns: 1fr;
    }
  }
</style>
