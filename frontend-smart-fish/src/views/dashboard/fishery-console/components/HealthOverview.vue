<template>
  <el-card shadow="never" class="health-overview">
    <template #header>
      <span class="font-bold">健康总览</span>
    </template>

    <div class="flex items-center justify-around py-4">
      <!-- 分数圆环 -->
      <div class="score-container">
        <el-progress
          type="dashboard"
          :percentage="score"
          :color="scoreColor"
          :width="120"
          :stroke-width="10"
        >
          <template #default="{ percentage }">
            <div class="flex flex-col items-center">
              <span class="text-3xl font-bold" :style="{ color: scoreColor }">{{
                percentage
              }}</span>
              <span class="text-xs text-g-500">综合健康度</span>
            </div>
          </template>
        </el-progress>
      </div>

      <!-- 风险等级 -->
      <div class="risks-container flex-1 ml-8">
        <div v-for="(level, type) in riskItems" :key="type" class="risk-item mb-4 last:mb-0">
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
    height: 100%;

    :deep(.el-card) {
      height: 100%;
    }

    :deep(.el-card__header) {
      padding: 16px;
    }

    :deep(.el-card__body) {
      display: flex;
      align-items: center;
      height: calc(100% - 57px);
      padding: 16px;
    }

    :deep(.el-progress-dashboard) {
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .score-container {
      flex-shrink: 0;
    }

    .risks-container {
      min-width: 0;
    }
  }

  @media (width <= 1200px) {
    .health-overview {
      :deep(.el-card__body) {
        height: auto;
      }

      .risks-container {
        margin-left: 16px;
      }
    }
  }
</style>
