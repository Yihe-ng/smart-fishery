<template>
  <el-card shadow="never" class="video-player-card">
    <template #header>
      <div class="flex-cb">
        <div class="flex-c gap-2">
          <ArtSvgIcon icon="ri:video-line" class="text-lg text-blue-500" />
          <span class="font-bold">实时视频监控</span>
        </div>
        <el-tag type="success" size="small" effect="dark">
          <ArtSvgIcon icon="ri:record-circle-line" class="animate-pulse mr-1" />LIVE
        </el-tag>
      </div>
    </template>

    <div class="video-container bg-black rounded overflow-hidden relative group">
      <!-- 视频元素 -->
      <video
        ref="videoRef"
        class="w-full aspect-video"
        :src="currentSource"
        autoplay
        muted
        playsinline
        @ended="handleVideoEnded"
      />

      <!-- 黑屏过渡层 -->
      <div
        v-show="isTransitioning"
        class="absolute inset-0 bg-black transition-opacity duration-300"
        :class="isTransitioning ? 'opacity-100' : 'opacity-0'"
      />

      <!-- 控制层 (模拟) -->
    </div>
  </el-card>
</template>

<script setup lang="ts">
  import { ref, computed, onMounted, onUnmounted, onActivated } from 'vue'
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'

  // Props 定义
  interface Props {
    /** 视频源列表 */
    sources: string[]
    /** 过渡动画时长（毫秒） */
    transitionDuration?: number
  }

  const props = withDefaults(defineProps<Props>(), {
    transitionDuration: 300
  })

  // 状态管理
  const videoRef = ref<HTMLVideoElement>()
  const currentIndex = ref(0)
  const isTransitioning = ref(false)
  const shuffledSources = ref<string[]>([])
  let transitionTimer: ReturnType<typeof setTimeout> | null = null

  // 当前播放的视频源
  const currentSource = computed(() => {
    if (shuffledSources.value.length === 0) return ''
    return shuffledSources.value[currentIndex.value]
  })

  /**
   * Fisher-Yates 洗牌算法
   * @param array 待洗牌的数组
   * @returns 洗牌后的新数组
   */
  const shuffleArray = <T,>(array: T[]): T[] => {
    const shuffled = [...array]
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1))
      ;[shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
    }
    return shuffled
  }

  /**
   * 播放下一个视频
   */
  const playNextVideo = () => {
    // 进入过渡状态
    isTransitioning.value = true

    transitionTimer = setTimeout(() => {
      // 更新索引
      currentIndex.value++

      // 如果播放完一轮，重新洗牌
      if (currentIndex.value >= shuffledSources.value.length) {
        shuffledSources.value = shuffleArray(props.sources)
        currentIndex.value = 0
      }

      // 退出过渡状态
      isTransitioning.value = false

      // 播放新视频
      videoRef.value?.play().catch(() => console.warn('Auto-play blocked'))
    }, props.transitionDuration)
  }

  /**
   * 视频结束事件处理
   */
  const handleVideoEnded = () => {
    playNextVideo()
  }

  /**
   * 恢复视频播放
   * 在组件从 KeepAlive 缓存激活时调用
   */
  const resumePlayback = () => {
    // 如果正在过渡中，不恢复播放
    if (isTransitioning.value) return

    // 检查视频元素存在且已暂停
    if (videoRef.value && videoRef.value.paused) {
      videoRef.value.play().catch(() => {
        // 浏览器自动播放策略阻止，静默处理
        console.log('Auto-play blocked by browser policy')
      })
    }
  }

  // 组件挂载时初始化
  onMounted(() => {
    if (props.sources.length > 0) {
      shuffledSources.value = shuffleArray(props.sources)
      currentIndex.value = 0
    }
  })

  // 组件从 KeepAlive 缓存激活时恢复播放
  onActivated(() => {
    resumePlayback()
  })

  // 组件卸载时清理
  onUnmounted(() => {
    if (transitionTimer) {
      clearTimeout(transitionTimer)
    }
  })
</script>

<style scoped lang="scss">
  .video-player-card {
    height: 100%;

    :deep(.el-card) {
      height: 100%;
    }

    :deep(.el-card__body) {
      height: calc(100% - 57px);
      padding: 12px;
    }

    .video-container {
      height: 100%;
    }
  }
</style>
