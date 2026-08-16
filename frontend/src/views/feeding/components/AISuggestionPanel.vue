<template>
  <el-card shadow="never" class="ai-suggestion-panel">
    <template #header>
      <div class="panel-header">
        <div class="title-wrap">
          <ArtSvgIcon icon="ri:deepseek-fill" class="title-icon" />
          <span class="title">生长与投喂建议</span>
        </div>
        <ElTag size="small" :type="panelTagType">{{ panelTagText }}</ElTag>
      </div>
    </template>

    <div class="panel-body" v-loading="loading">
      <!-- 生长结论区：第一优先级，位于全部投喂建议之上（方案 §8.1） -->
      <section v-if="growthSummary" class="growth-block" :class="growthBlockClass">
        <div class="growth-head">
          <div>
            <h4>{{ cohortText }}</h4>
            <p class="growth-meta">
              最近一次成功识别：{{ recognizedAtText }}
              <template v-if="growthExpired">｜已过期，仅供参考</template>
            </p>
          </div>
          <ElTag :type="cohortTagType" effect="light">{{ cohortLabel }}</ElTag>
        </div>

        <div class="growth-metrics">
          <div class="growth-metric">
            <span>{{ growthMetricLabel }}</span>
            <strong>{{ formatLengthCm(growthSummary.trimmedMeanLengthCm) }} cm</strong>
          </div>
          <div class="growth-metric">
            <span>本月参考范围</span>
            <strong>{{ referenceRangeText }}</strong>
          </div>
          <div class="growth-metric">
            <span>偏离比例</span>
            <strong>{{ deviationText }}</strong>
          </div>
        </div>

        <ul class="rationale-list">
          <li v-for="reason in growthRationale" :key="reason">{{ reason }}</li>
        </ul>

        <p v-if="growthExpired" class="growth-advice muted">
          识别结果已超过 24 小时，暂不生成新的投喂方向，请重新进行生长识别。
        </p>
        <p v-else-if="growthSummary.advice" class="growth-advice">
          {{ growthSummary.advice }}
        </p>

        <div class="growth-actions">
          <ElButton type="primary" size="small" @click="goGrowthRecognition">
            重新进行生长识别
          </ElButton>
          <ElButton size="small" @click="continueGrowthAnalysis">继续分析</ElButton>
        </div>
      </section>

      <section v-else class="empty-state">
        <ArtSvgIcon icon="ri:scales-3-line" size="24" />
        <p>暂无生长识别结果，先完成一次图片或视频生长识别才能生成生长与投喂建议。</p>
        <ElButton type="primary" size="small" @click="goGrowthRecognition">前往生长识别</ElButton>
      </section>

      <div class="panel-meta">
        <span>状态：{{ modeLabel }}</span>
        <span v-if="latestUpdatedAt">更新时间：{{ latestUpdatedAt }}</span>
      </div>

      <article
        v-for="card in visibleCards"
        :key="card.id"
        class="suggestion-card"
        :class="card.severity"
      >
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

        <div class="card-footer">
          <div class="metrics">
            <span>{{ card.updatedAt }}</span>
          </div>
          <div class="actions">
            <ElButton type="primary" size="small" @click="continueInAssistant(card)">
              继续分析
            </ElButton>
          </div>
        </div>
      </article>
    </div>
  </el-card>
</template>

<script setup lang="ts">
  import { useRouter } from 'vue-router'
  import { fetchFeedingSuggestions } from '@/api/agent'
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import { AI_MODE_LABEL } from '@/config/ai'
  import { useAIStore } from '@/store/modules/ai'
  import {
    DEFAULT_GROWTH_POND_ID,
    useGrowthRecognitionStore
  } from '@/store/modules/growth-recognition'
  import { useGrowthSummaryHydration } from '@/composables/useGrowthSummaryHydration'
  import type { AISeverity, AISuggestionCard } from '@/types'
  import {
    GROWTH_COHORT_STATUS_LABEL,
    GROWTH_COHORT_STATUS_TEXT,
    getGrowthCohortTagType
  } from '@/views/growth-monitoring/detect/constants/statusColors'
  import { formatLengthCm } from '@/views/growth-monitoring/detect/constants/assessmentParams'

  const props = defineProps<{
    pondId?: string
    currentIndex?: number
  }>()

  const router = useRouter()
  const aiStore = useAIStore()
  const growthRecognitionStore = useGrowthRecognitionStore()
  const loading = ref(false)
  const cards = ref<AISuggestionCard[]>([])
  const panelState = ref({ hasNewRisk: false, hasNewSuggestion: false })

  /** 保留水质与设备建议，只在展示层移除具体建议投喂克数。 */
  const sanitizeFeedingAmountText = (text: string) =>
    text.replace(/(?:推荐|建议)投喂量(?:约|为)?\s*\d+(?:\.\d+)?\s*g[，,]?\s*/gi, '').trim()

  const visibleCards = computed(() =>
    cards.value.map((card) => ({
      ...card,
      summary: sanitizeFeedingAmountText(card.summary),
      rationale: card.rationale
        .map(sanitizeFeedingAmountText)
        .filter((reason) => reason.length > 0),
      suggestedAmount: undefined
    }))
  )

  const activePondId = computed(() => props.pondId || DEFAULT_GROWTH_POND_ID)
  // 本地缓存为空或库里有更新记录时，从数据库恢复最近识别摘要
  useGrowthSummaryHydration(activePondId)
  const growthSummary = computed(() => growthRecognitionStore.getLatestSummary(activePondId.value))
  const growthExpired = computed(() => growthRecognitionStore.isSummaryExpired(growthSummary.value))

  const cohortStatus = computed(() => growthSummary.value?.cohortStatus ?? 'unassessed')
  const cohortLabel = computed(() => GROWTH_COHORT_STATUS_LABEL[cohortStatus.value])
  const cohortText = computed(() => GROWTH_COHORT_STATUS_TEXT[cohortStatus.value])
  const cohortTagType = computed(() => getGrowthCohortTagType(cohortStatus.value))
  const growthBlockClass = computed(() => ({ expired: growthExpired.value }))
  const growthMetricLabel = computed(() =>
    growthSummary.value?.sourceType === 'video' ? '视频群体评价全长' : '群体评价平均全长'
  )

  const recognizedAtText = computed(() => {
    if (!growthSummary.value?.recognizedAt) return '--'
    return new Date(growthSummary.value.recognizedAt).toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  })

  const referenceRangeText = computed(() => {
    const summary = growthSummary.value
    if (!summary || summary.smallThresholdCm == null || summary.largeThresholdCm == null) {
      return '--'
    }
    return `${formatLengthCm(summary.smallThresholdCm)}–${formatLengthCm(summary.largeThresholdCm)} cm`
  })

  // 偏离比例 = （群体评价平均全长 - 综合参考全长）/ 综合参考全长，保留一位小数并带正负号。
  const deviationText = computed(() => {
    const summary = growthSummary.value
    if (!summary?.trimmedMeanLengthCm || !summary.referenceLengthCm) return '--'

    const ratio =
      ((summary.trimmedMeanLengthCm - summary.referenceLengthCm) / summary.referenceLengthCm) * 100
    const sign = ratio > 0 ? '+' : ''
    return `${sign}${ratio.toFixed(1)}%`
  })

  /** 判断依据：只陈述已有的测量事实与参考口径，不假设投喂、水质、密度和健康数据 */
  const growthRationale = computed(() => {
    const summary = growthSummary.value
    if (!summary) return []

    const items: string[] = []

    if (summary.cultureMonth && summary.stockingAvgLengthCm != null) {
      items.push(
        `投苗后第 ${summary.cultureMonth} 个月，投苗时平均全长 ${formatLengthCm(summary.stockingAvgLengthCm)} cm`
      )
    } else {
      items.push('本次识别未提供养殖月数，仅完成体长测量')
    }

    if (summary.referenceLengthCm != null) {
      items.push(`本月综合参考全长 ${formatLengthCm(summary.referenceLengthCm)} cm`)
    }

    if (summary.sourceType === 'video') {
      const completed = summary.completedFrameCount ?? 0
      const planned = summary.plannedFrameCount ?? completed
      const evaluable = summary.evaluableFrameCount ?? 0
      items.push(`基于已完成 ${completed}/${planned} 个关键帧，其中 ${evaluable} 个可评价`)
      items.push(
        `累计鱼体检测 ${summary.detectionOccurrenceCount ?? summary.detectedCount} 次，可测 ${summary.measurableOccurrenceCount ?? summary.measurableCount} 次，不可测 ${summary.unmeasurableCount} 次`
      )
    } else {
      items.push(
        `识别总数 ${summary.detectedCount} 条，可测 ${summary.measurableCount} 条，不可测 ${summary.unmeasurableCount} 条`
      )
    }

    if (summary.allMeasurableAvgLengthCm != null) {
      items.push(`全部可测鱼平均全长 ${formatLengthCm(summary.allMeasurableAvgLengthCm)} cm`)
    }

    return items
  })

  const latestUpdatedAt = computed(() => visibleCards.value[0]?.updatedAt ?? '')
  const modeLabel = computed(() => {
    const mode = visibleCards.value[0]?.sourceMode ?? cards.value[0]?.sourceMode ?? 'mock'
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

  const goGrowthRecognition = () => {
    router.push('/fishery/growth')
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

  const continueGrowthAnalysis = async () => {
    await aiStore.openAssistant(
      {
        pageId: 'feeding',
        routePath: '/fishery/feeding',
        pondId: props.pondId,
        currentIndex: props.currentIndex
      },
      {
        activeTab: 'chat',
        initialPrompt: `请结合本页的群体生长结论"${cohortText.value}"继续分析后续管理方向。`
      }
    )
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
  .suggestion-head,
  .growth-head {
    display: flex;
    gap: 10px;
    align-items: center;
    justify-content: space-between;
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
    flex-direction: column;
    gap: 12px;
    height: 100%;
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
    flex-direction: column;
    gap: 8px;
    align-items: center;
    justify-content: center;
    min-height: 180px;
    padding: 16px;
    text-align: center;
    color: var(--el-text-color-secondary);
    border: 1px dashed var(--art-card-border);
    border-radius: 14px;

    p {
      max-width: 320px;
      margin: 0;
      line-height: 1.6;
    }
  }

  .growth-block {
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 14px;
    background: color-mix(in srgb, var(--el-color-primary) 6%, var(--default-box-color));
    border: 1px solid color-mix(in srgb, var(--el-color-primary) 20%, transparent);
    border-radius: 16px;
  }

  .growth-block.expired {
    background: color-mix(in srgb, var(--el-color-warning) 7%, var(--default-box-color));
    border-color: rgb(245 158 11 / 35%);
  }

  .growth-head {
    align-items: flex-start;
  }

  .growth-head h4 {
    margin: 0 0 6px;
    font-size: 15px;
  }

  .growth-meta {
    margin: 0;
    font-size: 12px;
    color: var(--el-text-color-secondary);
  }

  .growth-metrics {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 8px;
  }

  .growth-metric {
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 0;
    padding: 10px;
    background: var(--art-hover-color);
    border-radius: 8px;

    span {
      font-size: 12px;
      color: var(--el-text-color-secondary);
    }

    strong {
      font-size: 15px;
      font-variant-numeric: tabular-nums;
      color: var(--el-text-color-primary);
    }
  }

  .growth-advice {
    margin: 0;
    font-size: 13px;
    line-height: 1.7;
    color: var(--el-text-color-regular);
  }

  .growth-advice.muted {
    color: var(--el-text-color-secondary);
  }

  .growth-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .suggestion-card {
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 14px;
    background: var(--default-box-color);
    border: 1px solid var(--art-card-border);
    border-radius: 16px;
  }

  .suggestion-card.warning {
    background: color-mix(in srgb, var(--el-color-warning) 7%, var(--default-box-color));
    border-color: rgb(245 158 11 / 35%);
  }

  .suggestion-card.critical {
    background: color-mix(in srgb, var(--el-color-danger) 7%, var(--default-box-color));
    border-color: rgb(239 68 68 / 35%);
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
    line-height: 1.6;
    color: var(--el-text-color-regular);
  }

  .rationale-list {
    padding-left: 18px;
    margin: 0;
    font-size: 13px;
    line-height: 1.6;
    color: var(--el-text-color-secondary);
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

  @media (width <= 768px) {
    .growth-metrics {
      grid-template-columns: 1fr;
    }
  }
</style>
