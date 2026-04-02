<template>
  <el-card class="growth-result-card">
    <template #header>
      <div class="card-header">
        <ArtSvgIcon icon="ri:file-list-3-line" />
        <span>当前识别结果</span>
      </div>
    </template>

    <template v-if="result">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="编号">第 {{ result.index }} 条鱼</el-descriptions-item>
        <el-descriptions-item label="生长状态">
          <el-tag :type="statusType">{{ result.statusText }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="体长">
          <span class="metric-value">{{ result.bodyLengthCm }}</span>
          <span class="metric-unit">cm</span>
        </el-descriptions-item>
        <el-descriptions-item label="估重">
          <span class="metric-value">{{ result.weightG }}</span>
          <span class="metric-unit">g</span>
        </el-descriptions-item>
        <el-descriptions-item label="置信度">
          {{ `${Math.round(result.confidence * 100)}%` }}
        </el-descriptions-item>
      </el-descriptions>
    </template>

    <el-empty v-else :description="emptyText" :image-size="96" class="empty-result" />
  </el-card>
</template>

<script setup lang="ts">
  import { computed } from 'vue'
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import type { GrowthDetectionItem } from '@/types/growth-monitoring'

  const props = withDefaults(
    defineProps<{
      result: GrowthDetectionItem | null
      emptyText?: string
    }>(),
    {
      emptyText: '上传图片或视频后可查看识别详情'
    }
  )

  const statusType = computed(() => {
    switch (props.result?.status) {
      case 'small':
        return 'warning'
      case 'normal':
        return 'success'
      case 'large':
        return 'primary'
      default:
        return 'info'
    }
  })
</script>

<style scoped lang="scss">
  .growth-result-card {
    margin-top: 16px;

    .card-header {
      display: flex;
      gap: 8px;
      align-items: center;
      font-weight: 700;
    }

    .metric-value {
      font-size: 28px;
      font-weight: 700;
      color: var(--el-text-color-primary);
    }

    .metric-unit {
      margin-left: 4px;
      color: var(--el-text-color-secondary);
    }

    .empty-result {
      padding: 16px 0;
    }
  }
</style>
