<template>
  <div v-if="visible" class="growth-detection-state" :class="variantClass">
    <div class="state-content">
      <template v-if="taskStatus === 'processing'">
        <p class="state-title">正在识别石斑鱼</p>
        <p class="state-description">模型推理中，请稍候...</p>
      </template>

      <template v-else-if="taskStatus === 'failed'">
        <p class="state-title">识别失败</p>
        <p class="state-description">{{ message || '请更换素材后重试' }}</p>
      </template>

      <template v-else-if="taskStatus === 'success' && hasImage && !hasDetections">
        <p class="state-title">未识别到石斑鱼</p>
        <p class="state-description">当前素材未检测到有效目标，请尝试更清晰的图片或关键帧。</p>
      </template>

      <template v-else-if="taskStatus === 'idle' && !hasImage">
        <p class="state-title">等待上传图片或视频</p>
        <p class="state-description">上传石斑鱼图片或视频后，可在这里查看带框识别结果。</p>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { computed } from 'vue'
  import type { GrowthTaskStatus } from '@/types/growth-monitoring'

  const props = defineProps<{
    taskStatus: GrowthTaskStatus
    hasImage: boolean
    hasDetections: boolean
    message?: string
  }>()

  const visible = computed(
    () =>
      (props.taskStatus === 'idle' && !props.hasImage) ||
      props.taskStatus === 'processing' ||
      props.taskStatus === 'failed' ||
      (props.taskStatus === 'success' && props.hasImage && !props.hasDetections)
  )

  const variantClass = computed(() => {
    if (props.taskStatus === 'failed') return 'is-error'
    if (props.taskStatus === 'success') return 'is-empty'
    if (props.taskStatus === 'processing') return 'is-processing'
    return 'is-idle'
  })
</script>

<style scoped lang="scss">
  .growth-detection-state {
    position: absolute;
    inset: 0;
    z-index: 4;
    display: flex;
    align-items: center;
    justify-content: center;
    pointer-events: none;
  }

  .state-content {
    max-width: 320px;
    padding: 18px 22px;
    text-align: center;
    background: var(--growth-detect-state-bg);
    backdrop-filter: blur(8px);
    border: 1px solid var(--growth-detect-state-border);
    border-radius: 16px;
    box-shadow: 0 14px 40px rgb(15 23 42 / 12%);
  }

  .state-title {
    margin: 0;
    font-size: 18px;
    font-weight: 700;
    color: var(--el-text-color-primary);
  }

  .state-description {
    margin: 8px 0 0;
    line-height: 1.6;
    color: var(--el-text-color-secondary);
  }

  .is-error .state-content {
    background: rgb(255 245 245 / 82%);
    border-color: rgb(245 108 108 / 28%);
  }

  .is-processing .state-content {
    background: rgb(245 250 255 / 78%);
    border-color: rgb(64 158 255 / 24%);
  }

  :global(html) {
    --growth-detect-state-bg: rgb(255 255 255 / 74%);
    --growth-detect-state-border: rgb(255 255 255 / 55%);
  }

  :global(html.dark) {
    --growth-detect-state-bg: rgb(21 31 48 / 72%);
    --growth-detect-state-border: rgb(84 110 151 / 24%);
  }
</style>
