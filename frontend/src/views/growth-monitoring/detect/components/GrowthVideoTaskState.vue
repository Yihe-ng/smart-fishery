<template>
  <el-card v-if="visible" class="growth-video-task-state">
    <div class="state-content">
      <div class="state-copy">
        <p class="state-title">{{ title }}</p>
        <p class="state-description">{{ description }}</p>
      </div>

      <div v-if="taskStatus === 'queued' || taskStatus === 'processing'" class="state-progress">
        <el-progress :percentage="progress" :stroke-width="10" />
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
  import { computed } from 'vue'
  import type { GrowthStats, GrowthVideoTaskStatus } from '@/types/growth-monitoring'

  const props = withDefaults(
    defineProps<{
      taskStatus: GrowthVideoTaskStatus | null
      progress: number
      filename?: string
      frameCount?: number
      aggregateStats?: GrowthStats | null
      errorMessage?: string
    }>(),
    {
      filename: '',
      frameCount: 0,
      aggregateStats: null,
      errorMessage: ''
    }
  )

  const visible = computed(() => Boolean(props.taskStatus))

  const title = computed(() => {
    switch (props.taskStatus) {
      case 'queued':
        return '视频任务已创建'
      case 'processing':
        return '正在抽取关键帧并识别石斑鱼'
      case 'failed':
        return '视频识别失败'
      case 'success':
        return '视频关键帧识别完成'
      default:
        return ''
    }
  })

  const description = computed(() => {
    switch (props.taskStatus) {
      case 'queued':
        return props.filename ? `已接收 ${props.filename}，正在排队处理。` : '视频已接收，正在排队处理。'
      case 'processing':
        return `当前进度 ${props.progress}% ，系统会按时间顺序提取关键帧。`
      case 'failed':
        return props.errorMessage || '视频解析失败，请更换视频后重试。'
      case 'success':
        return `已提取 ${props.frameCount} 张关键帧，累计识别 ${props.aggregateStats?.detectedCount ?? 0} 条鱼。`
      default:
        return ''
    }
  })
</script>

<style scoped lang="scss">
  .growth-video-task-state {
    margin-top: 16px;
  }

  .state-content {
    display: flex;
    gap: 16px;
    align-items: center;
    justify-content: space-between;
  }

  .state-copy {
    min-width: 0;
  }

  .state-title {
    margin: 0;
    font-size: 16px;
    font-weight: 700;
    color: var(--el-text-color-primary);
  }

  .state-description {
    margin: 6px 0 0;
    line-height: 1.6;
    color: var(--el-text-color-secondary);
  }

  .state-progress {
    width: min(240px, 40%);
    min-width: 180px;
  }

  @media (max-width: 768px) {
    .state-content {
      flex-direction: column;
      align-items: stretch;
    }

    .state-progress {
      width: 100%;
      min-width: 0;
    }
  }
</style>
