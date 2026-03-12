<template>
  <el-card class="detect-image-display" :body-style="{ padding: '0px' }">
    <div class="display-container">
      <div v-if="!src" class="empty-state">
        <ArtSvgIcon icon="ri:image-line" class="text-6xl text-blue-500" />
        <p class="empty-text">等待输入源</p>
        <el-text type="info">请上传本地图像或接入实时摄像头流</el-text>
      </div>
      <template v-else>
        <img v-if="!isStream" :src="src" alt="病害检测图像" class="display-content" />
        <video v-else ref="videoRef" class="display-content" autoplay muted playsinline />

        <!-- 删除按钮 -->
        <div class="action-overlay" v-if="!isStream">
          <el-button type="danger" circle size="small" @click="emit('delete')">
            <template #icon>
              <ArtSvgIcon icon="ri:delete-bin-line" />
            </template>
          </el-button>
        </div>
      </template>

      <!-- 装饰性水波纹元素 (示例) -->
      <div class="water-ripple" v-if="isStream"></div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
  import { ref, watch, onMounted, onUnmounted } from 'vue'
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import Hls from 'hls.js'

  const props = defineProps<{
    src: string | null
    isStream: boolean
  }>()

  const emit = defineEmits<{
    delete: []
  }>()

  const videoRef = ref<HTMLVideoElement>()
  let hls: Hls | null = null

  const initHls = () => {
    if (hls) {
      hls.destroy()
      hls = null
    }

    if (props.src && props.isStream && videoRef.value) {
      if (Hls.isSupported()) {
        hls = new Hls()
        hls.loadSource(props.src)
        hls.attachMedia(videoRef.value)
        hls.on(Hls.Events.MANIFEST_PARSED, () => {
          videoRef.value?.play().catch(() => console.log('Auto-play blocked'))
        })
      } else if (videoRef.value.canPlayType('application/vnd.apple.mpegurl')) {
        videoRef.value.src = props.src
        videoRef.value.addEventListener('loadedmetadata', () => {
          videoRef.value?.play()
        })
      }
    }
  }

  watch(
    () => props.src,
    () => {
      if (props.isStream) {
        // 使用 nextTick 确保 videoRef 已更新
        setTimeout(initHls, 0)
      }
    }
  )

  onMounted(() => {
    if (props.isStream) initHls()
  })

  onUnmounted(() => {
    if (hls) {
      hls.destroy()
      hls = null
    }
  })
</script>

<style scoped lang="scss">
  .detect-image-display {
    width: 100%;
    overflow: hidden;

    .display-container {
      position: relative;
      display: flex;
      align-items: center;
      justify-content: center;
      width: 100%;
      aspect-ratio: 16 / 9;
      background: var(--el-fill-color-darker);

      .empty-state {
        text-align: center;

        .empty-text {
          margin: 16px 0 8px;
          font-size: 18px;
          font-weight: bold;
          color: var(--el-text-color-primary);
        }
      }

      .display-content {
        max-width: 100%;
        max-height: 100%;
        object-fit: contain;
      }

      .action-overlay {
        position: absolute;
        top: 12px;
        right: 12px;
        z-index: 10;
        opacity: 0;
        transition: opacity 0.3s;
      }

      &:hover .action-overlay {
        opacity: 1;
      }

      .water-ripple {
        position: absolute;
        right: 20px;
        bottom: 20px;
        width: 40px;
        height: 40px;
        pointer-events: none;
        background: rgb(64 158 255 / 20%);
        border-radius: 50%;
        animation: ripple 2s infinite;
      }
    }
  }

  @keyframes ripple {
    0% {
      opacity: 0.8;
      transform: scale(1);
    }

    100% {
      opacity: 0;
      transform: scale(2.5);
    }
  }
</style>
