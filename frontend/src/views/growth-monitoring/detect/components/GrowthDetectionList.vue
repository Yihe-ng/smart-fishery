<template>
  <el-card class="growth-detection-list">
    <template #header>
      <div class="card-header">
        <ArtSvgIcon icon="ri:list-check-3" />
        <span>鱼列表</span>
      </div>
    </template>

    <el-empty
      v-if="!detections.length"
      description="当前没有可切换的识别目标"
      :image-size="72"
    />

    <div v-else class="list-body">
      <button
        v-for="item in detections"
        :key="item.id"
        type="button"
        class="list-item"
        :class="{ active: item.id === selectedId }"
        @click="emit('select', item.id)"
      >
        <span class="item-index">第 {{ item.index }} 条鱼</span>
        <span class="item-status">{{ item.statusText }}</span>
        <span class="item-length">{{ item.bodyLengthCm }}cm</span>
      </button>
    </div>
  </el-card>
</template>

<script setup lang="ts">
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import type { GrowthDetectionItem } from '@/types/growth-monitoring'

  defineProps<{
    detections: GrowthDetectionItem[]
    selectedId: string | null
  }>()

  const emit = defineEmits<{
    select: [id: string]
  }>()
</script>

<style scoped lang="scss">
  .growth-detection-list {
    display: flex;
    flex-direction: column;
    margin-top: 16px;
    overflow: hidden;

    :deep(.el-card__body) {
      display: flex;
      flex: 1;
      flex-direction: column;
      min-height: 0;
      overflow: hidden;
    }

    .card-header {
      display: flex;
      gap: 8px;
      align-items: center;
      font-weight: 700;
    }

    .list-body {
      display: flex;
      flex: 1;
      flex-direction: column;
      gap: 10px;
      min-height: 0;
      padding-right: 4px;
      overflow-x: hidden;
      overflow-y: auto;
      scrollbar-color: var(--art-card-border) transparent;
      scrollbar-width: thin;
    }

    .list-body::-webkit-scrollbar {
      width: 6px;
    }

    .list-body::-webkit-scrollbar-track {
      background: transparent;
    }

    .list-body::-webkit-scrollbar-thumb {
      background: var(--art-card-border);
      border-radius: 999px;
    }

    .list-body::-webkit-scrollbar-thumb:hover {
      background: var(--el-border-color);
    }

    .list-item {
      display: grid;
      grid-template-columns: 1.2fr 0.8fr 0.7fr;
      gap: 8px;
      align-items: center;
      width: 100%;
      padding: 10px 12px;
      cursor: pointer;
      color: var(--el-text-color-primary);
      background: var(--el-fill-color-light);
      border: 1px solid transparent;
      border-radius: 10px;
      transition: all 0.2s ease;
    }

    .list-item:hover,
    .list-item.active {
      background: rgb(64 158 255 / 8%);
      border-color: rgb(64 158 255 / 40%);
    }

    .item-index {
      font-weight: 600;
    }

    .item-status,
    .item-length {
      text-align: right;
      color: var(--el-text-color-secondary);
    }
  }
</style>
