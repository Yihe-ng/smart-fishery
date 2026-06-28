<template>
  <el-card shadow="never" class="growth-summary-card" :class="{ compact }">
    <template #header>
      <div class="card-header">
        <div class="title-wrap">
          <ArtSvgIcon icon="ri:scales-3-line" class="title-icon" />
          <span class="font-bold">{{ title }}</span>
        </div>
        <el-tag v-if="summary" :type="expired ? 'warning' : 'success'" effect="plain" size="small">
          {{ expired ? '可能过期' : '已更新' }}
        </el-tag>
      </div>
    </template>

    <div v-if="summary" class="summary-content">
      <div class="summary-topline">
        <div>
          <div class="summary-number">{{ summary.detectedCount }}</div>
          <div class="summary-label">识别总数</div>
        </div>
        <div class="summary-meta">
          <span>{{ sourceText }}</span>
          <span>最近一次成功识别：{{ recognizedAtText }}</span>
        </div>
      </div>

      <div class="metrics-grid">
        <div class="metric-item">
          <span class="metric-label">可测比例</span>
          <strong>{{ summary.measurableRatio }}%</strong>
        </div>
        <div class="metric-item">
          <span class="metric-label">平均体长</span>
          <strong>{{ formatNumber(summary.avgBodyLengthCm) }}cm</strong>
        </div>
        <div class="metric-item">
          <span class="metric-label">平均估重</span>
          <strong>{{ formatNumber(summary.avgWeightG) }}g</strong>
        </div>
      </div>

      <div class="distribution">
        <div class="distribution-item small">
          <span>偏小</span>
          <strong>{{ summary.small }}</strong>
        </div>
        <div class="distribution-item normal">
          <span>正常</span>
          <strong>{{ summary.normal }}</strong>
        </div>
        <div class="distribution-item large">
          <span>偏大</span>
          <strong>{{ summary.large }}</strong>
        </div>
      </div>

      <div v-if="expired" class="summary-warning">
        <ArtSvgIcon icon="ri:time-line" />
        <span>识别结果可能已过期，仅供参考</span>
      </div>
    </div>

    <div v-else class="empty-state">
      <div class="empty-icon">
        <ArtSvgIcon icon="ri:image-add-line" />
      </div>
      <div class="empty-title">暂无生长识别结果</div>
      <p>请先上传图片或视频完成识别，系统将基于鱼体规格提供投喂辅助参考。</p>
      <el-button type="primary" size="small" @click="goGrowthRecognition">
        <template #icon>
          <ArtSvgIcon icon="ri:arrow-right-line" />
        </template>
        去生长识别
      </el-button>
    </div>
  </el-card>
</template>

<script setup lang="ts">
  import { computed } from 'vue'
  import { useRouter } from 'vue-router'
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import {
    DEFAULT_GROWTH_POND_ID,
    useGrowthRecognitionStore
  } from '@/store/modules/growth-recognition'

  const props = withDefaults(
    defineProps<{
      pondId?: string
      title?: string
      compact?: boolean
    }>(),
    {
      title: '最近生长识别参考',
      compact: false
    }
  )

  const router = useRouter()
  const growthRecognitionStore = useGrowthRecognitionStore()

  const activePondId = computed(() => props.pondId || DEFAULT_GROWTH_POND_ID)
  const summary = computed(() => growthRecognitionStore.getLatestSummary(activePondId.value))
  const expired = computed(() => growthRecognitionStore.isSummaryExpired(summary.value))

  const sourceText = computed(() => {
    if (!summary.value) return ''
    if (summary.value.sourceType === 'video') return '视频任务'
    return summary.value.isDemoData ? '示例图片' : '用户上传图片'
  })

  const recognizedAtText = computed(() => {
    if (!summary.value?.recognizedAt) return '--'
    return new Date(summary.value.recognizedAt).toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  })

  const formatNumber = (value: number) => {
    if (!Number.isFinite(value)) return '--'
    return Number(value.toFixed(1))
  }

  const goGrowthRecognition = () => {
    router.push('/fishery/growth')
  }
</script>

<style scoped lang="scss">
  .growth-summary-card {
    height: 100%;

    :deep(.el-card__header) {
      padding: 14px 16px;
      border-bottom: 1px solid var(--art-card-border);
    }

    :deep(.el-card__body) {
      height: calc(100% - 53px);
      padding: 16px;
    }

    .card-header,
    .title-wrap {
      display: flex;
      gap: 8px;
      align-items: center;
      justify-content: space-between;
    }

    .title-wrap {
      justify-content: flex-start;
      color: var(--el-text-color-primary);
    }

    .title-icon {
      color: var(--el-color-primary);
    }

    .summary-content {
      display: flex;
      flex-direction: column;
      gap: 14px;
      height: 100%;
      min-height: 0;
    }

    .summary-topline {
      display: flex;
      gap: 12px;
      align-items: flex-start;
      justify-content: space-between;
      padding: 12px;
      background: color-mix(in srgb, var(--el-color-primary) 9%, transparent);
      border: 1px solid color-mix(in srgb, var(--el-color-primary) 18%, transparent);
      border-radius: 8px;
    }

    .summary-number {
      font-size: 32px;
      font-weight: 800;
      font-variant-numeric: tabular-nums;
      line-height: 1;
      color: var(--el-color-primary);
    }

    .summary-label,
    .metric-label,
    .summary-meta,
    .distribution-item span {
      font-size: 12px;
      color: var(--el-text-color-secondary);
    }

    .summary-meta {
      display: flex;
      flex-direction: column;
      gap: 4px;
      align-items: flex-end;
      text-align: right;
    }

    .metrics-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
    }

    .metric-item {
      display: flex;
      flex-direction: column;
      gap: 4px;
      min-width: 0;
      padding: 10px;
      background: var(--art-hover-color);
      border-radius: 8px;

      strong {
        font-size: 17px;
        font-variant-numeric: tabular-nums;
        color: var(--el-text-color-primary);
      }
    }

    .distribution {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 8px;
    }

    .distribution-item {
      display: flex;
      gap: 8px;
      align-items: center;
      justify-content: space-between;
      padding: 9px 10px;
      background: var(--default-bg-color);
      border: 1px solid var(--art-card-border);
      border-radius: 8px;

      strong {
        font-size: 16px;
        font-variant-numeric: tabular-nums;
        color: var(--el-text-color-primary);
      }

      &.small {
        border-left: 3px solid var(--el-color-warning);
      }

      &.normal {
        border-left: 3px solid var(--el-color-success);
      }

      &.large {
        border-left: 3px solid var(--el-color-danger);
      }
    }

    .summary-warning {
      display: flex;
      gap: 6px;
      align-items: center;
      padding: 8px 10px;
      margin-top: auto;
      font-size: 12px;
      color: var(--el-color-warning);
      background: color-mix(in srgb, var(--el-color-warning) 10%, transparent);
      border-radius: 8px;
    }

    .empty-state {
      display: flex;
      flex-direction: column;
      gap: 10px;
      align-items: center;
      justify-content: center;
      height: 100%;
      min-height: 210px;
      text-align: center;

      p {
        max-width: 280px;
        margin: 0;
        font-size: 13px;
        line-height: 1.6;
        color: var(--el-text-color-secondary);
      }
    }

    .empty-icon {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 48px;
      height: 48px;
      font-size: 24px;
      color: var(--el-color-primary);
      background: color-mix(in srgb, var(--el-color-primary) 10%, transparent);
      border-radius: 50%;
    }

    .empty-title {
      font-size: 15px;
      font-weight: 700;
      color: var(--el-text-color-primary);
    }

    &.compact {
      :deep(.el-card__body) {
        padding: 14px;
        overflow-y: auto;
      }

      .empty-state {
        min-height: 180px;
      }

      .summary-content {
        gap: 12px;
      }

      .summary-number {
        font-size: 28px;
      }
    }
  }

  @media (width <= 768px) {
    .growth-summary-card {
      .summary-topline,
      .summary-meta {
        align-items: flex-start;
        text-align: left;
      }

      .summary-topline {
        flex-direction: column;
      }

      .metrics-grid,
      .distribution {
        grid-template-columns: 1fr;
      }
    }
  }
</style>
