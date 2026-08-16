<template>
  <el-card v-if="visible" class="growth-video-task-state">
    <div class="state-content">
      <div class="state-copy">
        <p class="state-title">{{ title }}</p>
        <p class="state-description">{{ description }}</p>
      </div>

      <div v-if="taskStatus === 'queued' || taskStatus === 'processing'" class="state-progress">
        <el-progress :percentage="progress" :stroke-width="10" />
        <el-button v-if="!isCancelling" type="danger" text size="small" @click="emit('cancel')">
          取消识别
        </el-button>
        <span v-else class="cancel-copy">正在取消</span>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
  import { computed } from 'vue'
  import type {
    GrowthStats,
    GrowthVideoTaskStage,
    GrowthVideoTaskStatus
  } from '@/types/growth-monitoring'

  defineOptions({ name: 'GrowthVideoTaskState' })

  const props = withDefaults(
    defineProps<{
      taskStatus: GrowthVideoTaskStatus | null
      stage: GrowthVideoTaskStage
      progress: number
      filename?: string
      frameCount?: number
      plannedFrameCount?: number
      completedFrameCount?: number
      evaluableFrameCount?: number
      detectionOccurrenceCount?: number
      aggregateStats?: GrowthStats | null
      errorMessage?: string
      isPartial?: boolean
      isCancelling?: boolean
    }>(),
    {
      filename: '',
      frameCount: 0,
      plannedFrameCount: 0,
      completedFrameCount: 0,
      evaluableFrameCount: 0,
      detectionOccurrenceCount: 0,
      aggregateStats: null,
      errorMessage: '',
      isPartial: false,
      isCancelling: false
    }
  )

  const emit = defineEmits<{
    cancel: []
  }>()

  const visible = computed(() => Boolean(props.taskStatus))

  const title = computed(() => {
    switch (props.taskStatus) {
      case 'queued':
        return '视频任务已创建'
      case 'processing':
        return props.stage === 'finalizing'
          ? '正在整理已完成的关键帧结果'
          : '正在抽取关键帧并识别石斑鱼'
      case 'failed':
        return '视频识别失败'
      case 'cancelled':
        return '视频识别已取消'
      case 'success':
        return props.isPartial ? '视频识别部分完成' : '视频关键帧识别完成'
      default:
        return ''
    }
  })

  const description = computed(() => {
    switch (props.taskStatus) {
      case 'queued':
        return props.filename
          ? `已接收 ${props.filename}，正在排队处理。`
          : '视频已接收，正在排队处理。'
      case 'processing':
        return props.stage === 'preparing'
          ? '正在准备模型与视频关键帧。'
          : `正在处理关键帧 ${props.completedFrameCount}/${props.plannedFrameCount}，其中 ${props.evaluableFrameCount} 个可评价。`
      case 'failed':
        return props.errorMessage || '视频解析失败，请更换视频后重试。'
      case 'cancelled':
        return `已保留 ${props.completedFrameCount} 个已完成关键帧，本次不生成视频级结论。`
      case 'success':
        return `已分析 ${props.completedFrameCount}/${props.plannedFrameCount} 个关键帧，其中 ${props.evaluableFrameCount} 个可评价，累计获得 ${props.detectionOccurrenceCount} 次鱼体检测。`
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

  .cancel-copy {
    display: block;
    margin-top: 6px;
    font-size: 12px;
    color: var(--el-color-danger);
  }

  @media (width <= 768px) {
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
