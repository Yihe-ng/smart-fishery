<template>
  <el-card shadow="never" class="ai-detection-card">
    <template #header>
      <div class="flex-cb">
        <div class="flex-c gap-2">
          <ArtSvgIcon icon="ri:scan-line" class="text-lg text-purple-500" />
          <span class="font-bold">AI 识别抓拍</span>
        </div>
      </div>
    </template>

    <div class="detection-container relative rounded overflow-hidden">
      <!-- 视频播放 -->
      <video
        ref="videoRef"
        class="w-full h-full object-cover"
        src="/video/识别示例视频.mp4"
        autoplay
        muted
        loop
        playsinline
      />
    </div>
  </el-card>
</template>

<script setup lang="ts">
  import { ref, onMounted, onUnmounted } from 'vue'
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'

  const videoRef = ref<HTMLVideoElement>()
  const currentTime = ref('')

  // 更新时间显示
  let timeTimer: ReturnType<typeof setInterval> | null = null

  const updateTime = () => {
    const now = new Date()
    currentTime.value = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`
  }

  onMounted(() => {
    updateTime()
    timeTimer = setInterval(updateTime, 1000)
  })

  onUnmounted(() => {
    if (timeTimer) clearInterval(timeTimer)
  })
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

      video {
        height: 100%;
        object-fit: cover;
      }
    }
  }
</style>
