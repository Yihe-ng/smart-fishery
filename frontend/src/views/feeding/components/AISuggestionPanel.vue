<template>
  <el-card shadow="never" class="ai-suggestion-panel">
    <template #header>
      <div class="panel-header">
        <div class="title-wrap">
          <ArtSvgIcon icon="ri:robot-2-line" class="text-[18px] text-sky-500" />
          <span class="font-bold">AI 建议栏</span>
        </div>
        <ElTag size="small" :type="panelTagType">{{ panelTagText }}</ElTag>
      </div>
    </template>

    <div class="panel-body" v-loading="loading">
      <div class="panel-meta">
        <span>数据模式：MOCK</span>
        <span v-if="latestUpdatedAt">更新时间：{{ latestUpdatedAt }}</span>
      </div>

      <div v-if="cards.length === 0" class="empty-state">
        <ArtSvgIcon icon="ri:message-3-line" size="24" />
        <p>当前没有可展示的 AI 建议。</p>
      </div>

      <article v-for="card in cards" :key="card.id" class="suggestion-card" :class="card.severity">
        <div class="suggestion-head">
          <div>
            <h4>{{ card.title }}</h4>
            <p>{{ card.summary }}</p>
          </div>
          <ElTag :type="getSeverityType(card.severity)" effect="light">{{ card.severity }}</ElTag>
        </div>

        <ul class="rationale-list">
          <li v-for="reason in card.rationale" :key="reason">{{ reason }}</li>
        </ul>

        <div class="card-footer">
          <div class="metrics">
            <span>{{ card.updatedAt }}</span>
          </div>
          <div class="actions">
            <ElButton text type="primary" @click="continueInAssistant(card)">查看依据</ElButton>
            <ElButton
              v-if="card.confirmRequired"
              text
              type="warning"
              @click="previewAction(card)"
            >
              生成预览
            </ElButton>
          </div>
        </div>
      </article>
    </div>
  </el-card>
</template>

<script setup lang="ts">
  import { fetchFeedingSuggestions } from '@/api/ai'
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import { useAIStore } from '@/store/modules/ai'
  import type { AISuggestionCard } from '@/types'

  const props = defineProps<{
    pondId?: string
  }>()

  const aiStore = useAIStore()
  const loading = ref(false)
  const cards = ref<AISuggestionCard[]>([])
  const panelState = ref({ hasNewRisk: false, hasNewSuggestion: false })

  const latestUpdatedAt = computed(() => cards.value[0]?.updatedAt ?? '')
  const panelTagText = computed(() => {
    if (panelState.value.hasNewRisk) return '有风险'
    if (panelState.value.hasNewSuggestion) return '有更新'
    return '稳定'
  })
  const panelTagType = computed(() => {
    if (panelState.value.hasNewRisk) return 'warning'
    if (panelState.value.hasNewSuggestion) return 'success'
    return 'info'
  })

  const getSeverityType = (severity: AISuggestionCard['severity']) => {
    if (severity === 'critical') return 'danger'
    if (severity === 'warning') return 'warning'
    return 'info'
  }

  const loadSuggestions = async () => {
    loading.value = true

    try {
      const response = await fetchFeedingSuggestions({
        pageId: 'feeding',
        routePath: '/fishery/feeding',
        pondId: props.pondId,
      })
      cards.value = response.cards
      panelState.value = response.panelState
    } finally {
      loading.value = false
    }
  }

  const continueInAssistant = async (card: AISuggestionCard) => {
    await aiStore.openAssistant(
      {
        pageId: 'feeding',
        routePath: '/fishery/feeding',
        pondId: props.pondId,
      },
      {
        activeTab: 'chat',
        initialPrompt: `请解释这条建议的依据，并结合当前页面上下文展开说明：${card.title}。建议摘要：${card.summary}`,
      },
    )
  }

  const previewAction = async (card: AISuggestionCard) => {
    await aiStore.openAssistant(
      {
        pageId: 'feeding',
        routePath: '/fishery/feeding',
        pondId: props.pondId,
      },
      {
        activeTab: 'automation',
        initialPrompt: `请为当前建议生成一次 600g 的手动投喂预览，并说明风险：${card.title}`,
      },
    )
  }

  onMounted(() => {
    loadSuggestions()
  })

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
    color: var(--el-text-color-secondary);
    border: 1px dashed var(--art-card-border);
    border-radius: 14px;
  }

  .suggestion-card {
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 14px;
    border-radius: 16px;
    border: 1px solid var(--art-card-border);
    background: var(--default-box-color);

    &.warning {
      border-color: rgb(245 158 11 / 35%);
      background: linear-gradient(180deg, rgb(245 158 11 / 7%), transparent);
    }

    &.critical {
      border-color: rgb(239 68 68 / 35%);
      background: linear-gradient(180deg, rgb(239 68 68 / 7%), transparent);
    }
  }

  .suggestion-head {
    align-items: flex-start;

    h4 {
      margin: 0 0 6px;
      font-size: 15px;
    }

    p {
      margin: 0;
      color: var(--el-text-color-regular);
      line-height: 1.6;
    }
  }

  .rationale-list {
    margin: 0;
    padding-left: 18px;
    color: var(--el-text-color-secondary);
    line-height: 1.6;
  }

  .card-footer {
    align-items: flex-end;
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
