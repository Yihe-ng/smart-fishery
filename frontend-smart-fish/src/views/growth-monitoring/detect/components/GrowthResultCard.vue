<template>
  <el-card class="growth-result-card" v-if="result">
    <template #header>
      <div class="card-header">
        <ArtSvgIcon icon="ri:file-list-3-line" />
        <span>当前识别结果</span>
      </div>
    </template>
    <el-descriptions :column="1" border>
      <el-descriptions-item label="生长状态">
        <el-tag :type="statusType">{{ statusText }}</el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="体长">
        <span class="text-lg font-bold">{{ result.bodyLength }}</span>
        <span class="text-gray-500 ml-1">cm</span>
      </el-descriptions-item>
      <el-descriptions-item label="估重">
        <span class="text-lg font-bold">{{ result.weight }}</span>
        <span class="text-gray-500 ml-1">g</span>
      </el-descriptions-item>
      <el-descriptions-item label="置信度">
        {{ (result.confidence * 100).toFixed(0) }}%
      </el-descriptions-item>
    </el-descriptions>
  </el-card>
</template>

<script setup lang="ts">
  import { computed } from 'vue'
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import type { GrowthDetectionItem } from '@/types/growth-monitoring'

  const props = defineProps<{
    result: GrowthDetectionItem | null
  }>()

  const statusType = computed(() => {
    switch (props.result?.class) {
      case 'small': return 'warning'
      case 'normal': return 'success'
      case 'large': return 'primary'
      default: return 'info'
    }
  })

  const statusText = computed(() => {
    switch (props.result?.class) {
      case 'small': return '偏小'
      case 'normal': return '正常'
      case 'large': return '偏大'
      default: return '未知'
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
      font-weight: bold;
    }
  }
</style>
