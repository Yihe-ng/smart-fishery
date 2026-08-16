<template>
  <el-card class="growth-cohort-card">
    <template #header>
      <div class="card-header">
        <div class="header-title">
          <ArtSvgIcon icon="ri:bar-chart-fill" />
          <span>群体生长评估</span>
        </div>
        <el-tag v-if="evaluating" type="warning" size="small" effect="plain">重新评价中</el-tag>
        <el-tag v-else-if="SHOW_GROWTH_STATUS_UI" :type="cohortTagType" size="small">
          {{ cohortLabel }}
        </el-tag>
      </div>
    </template>

    <p v-if="SHOW_GROWTH_STATUS_UI" class="cohort-conclusion">{{ cohortText }}</p>

    <div v-if="showCohortMean" class="primary-metric">
      <div class="metric-value">
        {{ formatLengthCm(assessment?.trimmedMeanLengthCm) }}
        <span class="metric-unit">cm</span>
      </div>
      <div class="metric-label">群体评价平均全长</div>
      <div class="metric-note">已去掉极端值</div>
    </div>

    <div v-if="showReferenceRange" class="reference-block">
      <div class="reference-row">
        <span>本月综合参考全长</span>
        <strong>{{ formatLengthCm(assessment?.referenceLengthCm) }} cm</strong>
      </div>
      <div class="reference-row">
        <span>正常参考范围</span>
        <strong>
          {{ formatLengthCm(assessment?.smallThresholdCm) }}–{{
            formatLengthCm(assessment?.largeThresholdCm)
          }}
          cm
        </strong>
      </div>
    </div>

    <div class="summary-footer">
      <span>全部可测鱼平均全长</span>
      <strong>{{ allMeasurableAvgText }} cm</strong>
    </div>

    <el-table v-if="SHOW_GROWTH_STATUS_UI && showDistribution" :data="tableData" style="width: 100%">
      <el-table-column prop="type" label="生长状态" />
      <el-table-column prop="count" label="数量" align="center">
        <template #default="{ row }">
          <el-tag :type="row.tagType">{{ row.count }}</el-tag>
        </template>
      </el-table-column>
    </el-table>

    <div class="summary-footer">
      <span>识别总数</span>
      <el-tag type="info">{{ stats.detectedCount }}</el-tag>
    </div>
    <div class="summary-footer compact">
      <span>可测 / 不可测</span>
      <span class="count-pair">
        <el-tag type="success">{{ stats.measurableCount }}</el-tag>
        <el-tag type="info">{{ stats.unmeasurableCount }}</el-tag>
      </span>
    </div>
  </el-card>
</template>

<script setup lang="ts">
  import { computed } from 'vue'
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import type { GrowthAssessment, GrowthStats, GrowthSummary } from '@/types/growth-monitoring'
  import {
    GROWTH_COHORT_STATUS_LABEL,
    GROWTH_COHORT_STATUS_TEXT,
    GROWTH_STATUS_TAG_TYPE,
    SHOW_GROWTH_STATUS_UI,
    getGrowthCohortTagType
  } from '../constants/statusColors'
  import { formatLengthCm, type CultureMonthSelection } from '../constants/assessmentParams'

  defineOptions({ name: 'GrowthStatsSummary' })

  const props = withDefaults(
    defineProps<{
      stats: GrowthStats
      assessment?: GrowthAssessment | null
      summary?: GrowthSummary | null
      cultureMonth?: CultureMonthSelection
      /** 轻量重评进行中：只在本卡片提示，图片与单鱼列表保持可用 */
      evaluating?: boolean
    }>(),
    {
      assessment: null,
      summary: null,
      cultureMonth: null,
      evaluating: false
    }
  )

  const cohortStatus = computed(() => props.assessment?.cohortStatus ?? 'unassessed')
  const cohortTagType = computed(() => getGrowthCohortTagType(cohortStatus.value))
  const cohortLabel = computed(() => GROWTH_COHORT_STATUS_LABEL[cohortStatus.value])
  const cohortText = computed(() => GROWTH_COHORT_STATUS_TEXT[cohortStatus.value])

  // 群体分档结论只在样本充足且已完成月度评价时展示（方案 §7.1）。
  const isAssessed = computed(() => cohortStatus.value !== 'unassessed')
  const showCohortMean = computed(
    () => isAssessed.value && props.assessment?.sampleSufficient === true
  )
  const showReferenceRange = computed(
    () => isAssessed.value && props.assessment?.referenceLengthCm !== null
  )
  const showDistribution = computed(() => isAssessed.value)

  // 后端未提供群体平均时退回普通平均体长，保证样本不足与未评估仍有数量与均值信息。
  const allMeasurableAvgText = computed(() =>
    formatLengthCm(props.assessment?.allMeasurableAvgLengthCm ?? props.summary?.avgBodyLengthCm)
  )

  const tableData = computed(() => [
    { type: '偏小', count: props.stats.small, tagType: GROWTH_STATUS_TAG_TYPE.small },
    { type: '正常', count: props.stats.normal, tagType: GROWTH_STATUS_TAG_TYPE.normal },
    { type: '偏大', count: props.stats.large, tagType: GROWTH_STATUS_TAG_TYPE.large }
  ])
</script>

<style scoped lang="scss">
  .growth-cohort-card {
    .card-header {
      display: flex;
      gap: 8px;
      align-items: center;
      justify-content: space-between;
      font-weight: 700;
    }

    .header-title {
      display: flex;
      gap: 8px;
      align-items: center;
    }

    .cohort-conclusion {
      margin: 0 0 12px;
      font-size: 13px;
      line-height: 1.6;
      color: var(--el-text-color-regular);
    }

    .primary-metric {
      padding: 12px;
      margin-bottom: 12px;
      text-align: center;
      background: var(--art-hover-color);
      border-radius: 8px;

      .metric-value {
        font-size: 28px;
        font-weight: 700;
        font-variant-numeric: tabular-nums;
        line-height: 1.2;
        color: var(--el-text-color-primary);
      }

      .metric-unit {
        margin-left: 4px;
        font-size: 14px;
        font-weight: 400;
        color: var(--el-text-color-secondary);
      }

      .metric-label {
        margin-top: 4px;
        font-size: 13px;
        color: var(--el-text-color-regular);
      }

      .metric-note {
        margin-top: 2px;
        font-size: 12px;
        color: var(--el-text-color-secondary);
      }
    }

    .reference-block {
      display: flex;
      flex-direction: column;
      gap: 6px;
      margin-bottom: 12px;
    }

    .reference-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-size: 13px;
      color: var(--el-text-color-secondary);

      strong {
        font-variant-numeric: tabular-nums;
        color: var(--el-text-color-primary);
      }
    }

    .summary-footer {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding-top: 12px;
      margin-top: 12px;
      color: var(--el-text-color-secondary);
      border-top: 1px solid var(--el-border-color-light);

      strong {
        font-variant-numeric: tabular-nums;
        color: var(--el-text-color-primary);
      }
    }

    .summary-footer.compact {
      padding-top: 8px;
      margin-top: 8px;
    }

    .count-pair {
      display: inline-flex;
      gap: 6px;
      align-items: center;
    }
  }
</style>
