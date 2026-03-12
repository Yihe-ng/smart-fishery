<template>
  <el-card shadow="never" class="ai-detection-card">
    <template #header>
      <div class="flex-cb">
        <div class="flex-c gap-2">
          <ArtSvgIcon icon="ri:scan-line" class="text-lg text-purple-500" />
          <span class="font-bold">AI 识别抓拍</span>
        </div>
        <span class="text-xs text-g-500">{{ formatTime(detection?.detectTime) }}</span>
      </div>
    </template>

    <div v-if="detection" class="detection-container relative rounded overflow-hidden">
      <img
        :src="detection.imageUrl"
        :alt="diseaseLabel ? `AI识别结果：${diseaseLabel}` : 'AI识别抓拍图'"
        class="w-full h-auto block"
      />

      <!-- 模拟检测框 -->
      <div class="detection-box absolute border-2 border-error bg-error/10" :style="boxStyle">
        <div class="absolute -top-6 left-0 px-1 bg-error text-white text-[10px] whitespace-nowrap">
          {{ diseaseLabel }} ({{ detection.confidence }}%)
        </div>
      </div>

      <!-- 底部信息 -->
      <div class="absolute bottom-0 left-0 right-0 p-2 bg-black/60 text-white text-xs flex-cb">
        <span>识别目标: 石斑鱼</span>
        <span>病害风险: {{ diseaseLabel }}</span>
      </div>
    </div>
    <el-empty v-else description="暂无识别记录" :image-size="80" />
  </el-card>
</template>

<script setup lang="ts">
  import { computed } from 'vue'
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import type { DetectionResult } from '@/types/fish-disease'

  const props = defineProps<{
    detection: DetectionResult | null
  }>()

  const diseaseLabel = computed(() => {
    const map: any = {
      gill_rot: '烂鳃病',
      red_skin: '赤皮病',
      enteritis: '肠炎病',
      healthy: '健康'
    }
    return map[props.detection?.diseaseType || ''] || '未知'
  })

  const boxStyle = computed(() => {
    if (!props.detection?.bbox) return { display: 'none' }
    const { x, y, width, height } = props.detection.bbox
    return {
      left: `${x}%`,
      top: `${y}%`,
      width: `${width}%`,
      height: `${height}%`
    }
  })

  const formatTime = (time?: string) => {
    if (!time) return ''
    const date = new Date(time)
    return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}:${date.getSeconds().toString().padStart(2, '0')}`
  }
</script>

<style scoped lang="scss">
  .ai-detection-card {
    height: 100%;

    :deep(.el-card) {
      height: 100%;
    }

    :deep(.el-card__body) {
      height: calc(100% - 57px);
      padding: 12px;
    }

    .detection-container {
      height: 100%;

      img {
        height: 100%;
        object-fit: cover;
      }
    }
  }
</style>
