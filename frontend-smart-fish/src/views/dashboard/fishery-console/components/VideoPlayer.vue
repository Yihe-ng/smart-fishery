<template>
  <el-card shadow="never" class="video-player-card">
    <template #header>
      <div class="flex-cb">
        <div class="flex-c gap-2">
          <ArtSvgIcon icon="ri:video-line" class="text-lg text-blue-500" />
          <span class="font-bold">实时视频监控 (模拟)</span>
        </div>
        <el-tag type="success" size="small" effect="dark">
          <ArtSvgIcon icon="ri:record-circle-line" class="animate-pulse mr-1" />LIVE
        </el-tag>
      </div>
    </template>

    <div class="video-container bg-black rounded overflow-hidden relative group">
      <video ref="videoRef" class="w-full aspect-video" autoplay muted playsinline></video>

      <!-- 叠加层 -->
      <div
        class="absolute top-2 left-2 px-2 py-1 bg-black/50 text-white text-xs rounded pointer-events-none"
      >
        Camera: Tank_P001_Front
      </div>

      <!-- 控制层 (模拟) -->
      <div
        class="absolute bottom-0 left-0 right-0 p-2 bg-gradient-to-t from-black/80 to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex-cb text-white"
      >
        <div class="flex-c gap-3">
          <ArtSvgIcon icon="ri:play-fill" class="cursor-pointer" />
          <ArtSvgIcon icon="ri:volume-mute-fill" class="cursor-pointer" />
        </div>
        <div class="flex-c gap-3">
          <ArtSvgIcon icon="ri:fullscreen-line" class="cursor-pointer" />
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
  import { ref, onMounted, onUnmounted, watch } from 'vue'
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import Hls from 'hls.js'

  const props = defineProps<{
    src: string
  }>()

  const videoRef = ref<HTMLVideoElement>()
  let hls: Hls | null = null

  const initHls = () => {
    if (hls) {
      hls.destroy()
      hls = null
    }

    if (props.src && videoRef.value) {
      if (Hls.isSupported()) {
        hls = new Hls()
        hls.loadSource(props.src)
        hls.attachMedia(videoRef.value)
        hls.on(Hls.Events.MANIFEST_PARSED, () => {
          videoRef.value?.play().catch(() => console.warn('Auto-play blocked'))
        })
      } else if (videoRef.value.canPlayType('application/vnd.apple.mpegurl')) {
        videoRef.value.src = props.src
        videoRef.value.addEventListener('loadedmetadata', () => {
          videoRef.value?.play()
        })
      }
    }
  }

  watch(() => props.src, initHls)

  onMounted(initHls)

  onUnmounted(() => {
    if (hls) {
      hls.destroy()
    }
  })
</script>

<style scoped lang="scss">
  .video-player-card {
    border: 1px solid var(--art-border-color);

    :deep(.el-card__body) {
      padding: 12px;
    }
  }
</style>
