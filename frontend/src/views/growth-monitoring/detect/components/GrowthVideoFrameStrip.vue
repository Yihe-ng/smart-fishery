<template>
  <el-card class="growth-video-frame-strip">
    <template #header>
      <div class="card-header">
        <ArtSvgIcon icon="ri:gallery-view-2" />
        <span>关键帧</span>
      </div>
    </template>

    <el-empty v-if="!frames.length" description="视频处理完成后将在这里展示关键帧" :image-size="72" />

    <div v-else class="frame-list">
      <button
        v-for="frame in frames"
        :key="frame.frameId"
        type="button"
        class="frame-item"
        :class="{ active: frame.frameId === selectedFrameId }"
        @click="emit('select', frame.frameId)"
      >
        <img :src="frame.image.src" :alt="`关键帧 ${frame.frameId}`" class="frame-thumb" />
        <div class="frame-meta">
          <span class="frame-time">{{ formatTimestamp(frame.timestampSec) }}</span>
          <span class="frame-count">{{ frame.stats.detectedCount }} 条鱼</span>
        </div>
      </button>
    </div>
  </el-card>
</template>

<script setup lang="ts">
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import type { GrowthVideoFrameItem } from '@/types/growth-monitoring'

  defineProps<{
    frames: GrowthVideoFrameItem[]
    selectedFrameId: string | null
  }>()

  const emit = defineEmits<{
    select: [frameId: string]
  }>()

  const formatTimestamp = (timestampSec: number) => {
    const minutes = Math.floor(timestampSec / 60)
    const seconds = timestampSec % 60
    return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
  }
</script>

<style scoped lang="scss">
  .growth-video-frame-strip {
    margin-top: 16px;

    .card-header {
      display: flex;
      gap: 8px;
      align-items: center;
      font-weight: 700;
    }
  }

  .frame-list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(148px, 1fr));
    gap: 12px;
  }

  .frame-item {
    display: flex;
    flex-direction: column;
    gap: 10px;
    padding: 10px;
    cursor: pointer;
    background: var(--el-fill-color-lighter);
    border: 1px solid transparent;
    border-radius: 14px;
    transition:
      transform 0.2s ease,
      border-color 0.2s ease,
      box-shadow 0.2s ease;
  }

  .frame-item:hover,
  .frame-item.active {
    border-color: rgb(54 207 201 / 38%);
    box-shadow: 0 10px 26px rgb(15 23 42 / 8%);
    transform: translateY(-1px);
  }

  .frame-thumb {
    width: 100%;
    aspect-ratio: 16 / 9;
    object-fit: cover;
    border-radius: 10px;
  }

  .frame-meta {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    font-size: 12px;
    color: var(--el-text-color-secondary);
  }

  .frame-time {
    font-weight: 600;
    color: var(--el-text-color-primary);
  }
</style>
