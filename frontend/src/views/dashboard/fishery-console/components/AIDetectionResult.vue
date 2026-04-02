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
  import { ref, onMounted, onUnmounted, onActivated } from 'vue'
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'

  const videoRef = ref<HTMLVideoElement>()
  const currentTime = ref('')

  // 更新时间显示
  let timeTimer: ReturnType<typeof setInterval> | null = null

  const updateTime = () => {
    const now = new Date()
    currentTime.value = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`
  }

  /**
   * 恢复视频播放
   * 在组件从 KeepAlive 缓存激活时调用
   */
  const resumePlayback = () => {
    if (videoRef.value && videoRef.value.paused) {
      videoRef.value.play().catch(() => {
        // 浏览器自动播放策略阻止，静默处理
        console.log('Auto-play blocked by browser policy')
      })
    }
  }

  onMounted(() => {
    updateTime()
    timeTimer = setInterval(updateTime, 1000)
  })

  // 组件从 KeepAlive 缓存激活时恢复播放
  onActivated(() => {
    resumePlayback()
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
