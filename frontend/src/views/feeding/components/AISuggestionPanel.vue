<template>
  <el-card shadow="never" class="ai-suggestion-panel">
    <template #header>
      <div class="panel-header">
        <div class="title-wrap">
          <ArtSvgIcon icon="ri:deepseek-fill" class="title-icon" />
          <span class="title">AI 投喂建议</span>
        </div>
        <ElTag size="small" :type="panelTagType">{{ panelTagText }}</ElTag>
      </div>
    </template>

    <div class="panel-body" v-loading="loading">
      <div class="panel-meta">
        <span>状态：{{ modeLabel }}</span>
        <span v-if="latestUpdatedAt">更新时间：{{ latestUpdatedAt }}</span>
      </div>

      <div v-if="cards.length === 0" class="empty-state">
        <ArtSvgIcon icon="ri:message-3-line" size="24" />
        <p>当前暂无投喂建议，请稍后刷新。</p>
      </div>

      <article v-for="card in cards" :key="card.id" class="suggestion-card" :class="card.severity">
        <div class="suggestion-head">
          <div>
            <h4>{{ card.title }}</h4>
            <p>{{ card.summary }}</p>
          </div>
          <ElTag :type="getSeverityType(card.severity)" effect="light">
            {{ severityText(card.severity) }}
          </ElTag>
        </div>

        <ul class="rationale-list">
          <li v-for="reason in card.rationale" :key="reason">{{ reason }}</li>
        </ul>

        <!-- 建议投喂量显示和采纳按钮 -->
        <div v-if="card.suggestedAmount" class="suggested-amount">
          <div class="amount-display">
            <span class="amount-label">建议投喂量</span>
            <span class="amount-value">{{ card.suggestedAmount }}g</span>
          </div>
          <ElButton type="primary" size="small" class="adopt-btn" @click="adoptSuggestion(card)">
            <ArtSvgIcon icon="ri:check-line" class="btn-icon" />
            采纳建议
          </ElButton>
        </div>

        <div class="card-footer">
          <div class="metrics">
            <span>{{ card.updatedAt }}</span>
          </div>
          <div class="actions">
            <ElButton type="primary" size="small" @click="continueInAssistant(card)">
              继续分析
            </ElButton>
            <ElButton
              v-if="card.confirmRequired"
              text
              type="warning"
              size="small"
              @click="previewAction()"
            >
              动作预览
            </ElButton>
          </div>
        </div>
      </article>
    </div>
  </el-card>
</template>

<script setup lang="ts">
  import { fetchFeedingSuggestions } from '@/api/agent'
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import { AI_MODE_LABEL } from '@/config/ai'
  import { useAIStore } from '@/store/modules/ai'
  import type { AISeverity, AISuggestionCard } from '@/types'

  const props = defineProps<{
    pondId?: string
    currentIndex?: number
  }>()

  const emit = defineEmits<{
    /** 采纳建议事件，传递建议投喂量 */
    (e: 'adopt-suggestion', amount: number): void
  }>()

  const aiStore = useAIStore()
  const loading = ref(false)
  const cards = ref<AISuggestionCard[]>([])
  const panelState = ref({ hasNewRisk: false, hasNewSuggestion: false })

  const latestUpdatedAt = computed(() => cards.value[0]?.updatedAt ?? '')
  const modeLabel = computed(() => {
    const mode = cards.value[0]?.sourceMode ?? 'mock'
    return AI_MODE_LABEL[mode]
  })

  const panelTagText = computed(() => {
    if (panelState.value.hasNewRisk) return '风险更新'
    if (panelState.value.hasNewSuggestion) return '建议更新'
    return '状态正常'
  })

  const panelTagType = computed(() => {
    if (panelState.value.hasNewRisk) return 'warning'
    if (panelState.value.hasNewSuggestion) return 'success'
    return 'info'
  })

  const getSeverityType = (severity: AISeverity) => {
    if (severity === 'critical') return 'danger'
    if (severity === 'warning') return 'warning'
    return 'info'
  }

  const severityText = (severity: AISeverity) => {
    if (severity === 'critical') return '高风险'
    if (severity === 'warning') return '中风险'
    return '低风险'
  }

  const loadSuggestions = async () => {
    loading.value = true
    try {
      const response = await fetchFeedingSuggestions({
        pageId: 'feeding',
        routePath: '/fishery/feeding',
        pondId: props.pondId,
        currentIndex: props.currentIndex
      })
      cards.value = response.cards
      panelState.value = response.panelState
    } finally {
      loading.value = false
    }
  }

  // 采纳建议
  const adoptSuggestion = (card: AISuggestionCard) => {
    if (card.suggestedAmount && card.suggestedAmount > 0) {
      emit('adopt-suggestion', card.suggestedAmount)
    }
  }

  const continueInAssistant = async (card: AISuggestionCard) => {
    await aiStore.openAssistant(
      {
        pageId: 'feeding',
        routePath: '/fishery/feeding',
        pondId: props.pondId,
        currentIndex: props.currentIndex
      },
      {
        activeTab: 'chat',
        initialPrompt: `请继续分析建议"${card.title}"，并结合当前页面数据给出处理建议：${card.summary}`
      }
    )
  }

  const previewAction = async () => {
    await aiStore.openAssistant(
      {
        pageId: 'feeding',
        routePath: '/fishery/feeding',
        pondId: props.pondId,
        currentIndex: props.currentIndex
      },
      {
        activeTab: 'automation'
      }
    )
    await aiStore.requestManualFeedingPreview(600)
  }

  watch(
    () => [props.pondId, props.currentIndex],
    () => {
      loadSuggestions()
    },
    { immediate: true }
  )
  defineExpose({ loadSuggestions })
</script>

<style scoped lang="scss">
  .ai-suggestion-panel {
    height: 100%;

    :deep(.el-card__body) {
      height: calc(100% - 57px);
      padding: 14px;
    }
  }

  .panel-header,
  .title-wrap,
  .card-footer,
  .actions,
  .metrics,
  .suggestion-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
  }

  .title-wrap {
    justify-content: flex-start;
  }

  .title {
    font-weight: 700;
  }

  .title-icon {
    font-size: 18px;
    line-height: 1;
    color: var(--el-text-color-primary);
  }

  .panel-body {
    display: flex;
    height: 100%;
    flex-direction: column;
    gap: 12px;
    overflow: auto;
  }

  .panel-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    font-size: 12px;
    color: var(--el-text-color-secondary);
  }

  .empty-state {
    display: flex;
    min-height: 180px;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 8px;
    border: 1px dashed var(--art-card-border);
    border-radius: 14px;
    color: var(--el-text-color-secondary);
  }

  .suggestion-card {
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 14px;
    border: 1px solid var(--art-card-border);
    border-radius: 16px;
    background: var(--default-box-color);
  }

  .suggestion-card.warning {
    border-color: rgb(245 158 11 / 35%);
    background: color-mix(in srgb, var(--el-color-warning) 7%, var(--default-box-color));
  }

  .suggestion-card.critical {
    border-color: rgb(239 68 68 / 35%);
    background: color-mix(in srgb, var(--el-color-danger) 7%, var(--default-box-color));
  }

  .suggestion-head {
    align-items: flex-start;
  }

  .suggestion-head h4 {
    margin: 0 0 6px;
    font-size: 15px;
  }

  .suggestion-head p {
    margin: 0;
    color: var(--el-text-color-regular);
    line-height: 1.6;
  }

  .rationale-list {
    margin: 0;
    padding-left: 18px;
    color: var(--el-text-color-secondary);
    line-height: 1.6;
    font-size: 13px;
  }

  // 建议投喂量和采纳按钮
  .suggested-amount {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 10px 12px;
    background: var(--el-color-primary-light-9);
    border-radius: 8px;
    border: 1px solid var(--el-color-primary-light-7);

    .amount-display {
      display: flex;
      flex-direction: column;
      gap: 2px;

      .amount-label {
        font-size: 11px;
        color: var(--el-text-color-secondary);
      }

      .amount-value {
        font-size: 18px;
        font-weight: 700;
        color: var(--el-color-primary);
      }
    }

    .adopt-btn {
      .btn-icon {
        margin-right: 4px;
        font-size: 14px;
      }
    }
  }

  .card-footer {
    align-items: flex-end;
    margin-top: 4px;
  }

  .metrics {
    flex-wrap: wrap;
    justify-content: flex-start;
    font-size: 12px;
    color: var(--el-text-color-secondary);
  }

  .actions {
    flex-shrink: 0;
  }
</style>
