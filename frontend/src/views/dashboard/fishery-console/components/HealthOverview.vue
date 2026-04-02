<template>
  <el-card shadow="never" class="health-overview">
    <template #header>
      <span class="font-bold">健康总览</span>
    </template>

    <div class="content-wrapper">
      <!-- 分数圆环 -->
      <div class="score-container">
        <el-progress
          type="dashboard"
          :percentage="score"
          :color="scoreColor"
          :width="140"
          :stroke-width="12"
        >
          <template #default="{ percentage }">
            <div class="flex flex-col items-center gap-0.5">
              <span
                class="text-4xl font-bold tracking-tight"
                :style="{ color: scoreColor, fontVariantNumeric: 'tabular-nums' }"
                >{{ percentage }}</span
              >
              <span
                class="text-xs font-medium tracking-wide"
                style="
                  color: var(--art-gray-500);
                  text-transform: uppercase;
                  letter-spacing: 0.08em;
                "
                >综合健康度</span
              >
            </div>
          </template>
        </el-progress>
      </div>

      <!-- 风险等级 -->
      <div class="risks-container">
        <div v-for="(level, type) in riskItems" :key="type" class="risk-item">
          <div class="flex-cb mb-1">
            <span class="text-sm text-g-600">{{ riskLabels[type] }}</span>
            <el-tag :type="getRiskTagType(level)" size="small" effect="plain">{{
              getRiskText(level)
            }}</el-tag>
          </div>
          <el-progress
            :percentage="getRiskPercentage(level)"
            :color="getRiskColor(level)"
            :show-text="false"
            :stroke-width="10"
          />
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
  import { computed } from 'vue'

  const props = defineProps<{
    score: number
    risks: {
      gillRot: 'low' | 'medium' | 'high'
      redSkin: 'low' | 'medium' | 'high'
      enteritis: 'low' | 'medium' | 'high'
    }
  }>()

  const riskItems = computed(() => props.risks)

  const riskLabels: any = {
    gillRot: '烂鳃风险',
    redSkin: '赤皮风险',
    enteritis: '肠炎风险'
  }

  const scoreColor = computed(() => {
    if (props.score >= 90) return 'var(--art-success)'
    if (props.score >= 70) return 'var(--art-warning)'
    return 'var(--art-danger)'
  })

  const getRiskTagType = (level: string) => {
    const map: any = { low: 'success', medium: 'warning', high: 'danger' }
    return map[level] || 'info'
  }

  const getRiskText = (level: string) => {
    const map: any = { low: '极低', medium: '中等', high: '极高' }
    return map[level] || '未知'
  }

  const getRiskPercentage = (level: string) => {
    const map: any = { low: 20, medium: 50, high: 90 }
    return map[level] || 0
  }

  const getRiskColor = (level: string) => {
    const map: any = {
      low: 'var(--art-success)',
      medium: 'var(--art-warning)',
      high: 'var(--art-danger)'
    }
    return map[level] || 'var(--art-gray-400)'
  }
</script>

<style scoped lang="scss">
  .health-overview {
    display: flex;
    flex-direction: column;
    height: 100%;

    :deep(.el-card) {
      display: flex;
      flex-direction: column;
      height: 100%;
    }

    :deep(.el-card__header) {
      flex-shrink: 0;
      padding: 16px;
    }

    :deep(.el-card__body) {
      display: flex;
      flex: 1;
      flex-direction: column;
      min-height: 0;
      padding: 16px;
    }

    .content-wrapper {
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex: 1;
      gap: 16px;
    }

    .score-container {
      flex-shrink: 0;
      display: flex;
      align-items: center;
    }

    .risks-container {
      flex: 1;
      display: flex;
      flex-direction: column;
      justify-content: space-around;
      min-width: 0;

      .risk-item {
        flex: 1;
        display: flex;
        flex-direction: column;
        justify-content: center;

        &:not(:last-child) {
          margin-bottom: 12px;
        }
      }
    }

    :deep(.el-progress__bar) {
      height: 10px !important;
    }
  }

  @media (width <= 1200px) {
    .health-overview {
      :deep(.el-card__body) {
        height: auto;
      }

      .content-wrapper {
        flex-direction: column;
        gap: 16px;
      }

      .risks-container {
        width: 100%;
      }
    }
  }
</style>
