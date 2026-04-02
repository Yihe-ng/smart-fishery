<template>
  <el-card class="detect-image-display" :body-style="{ padding: '0px' }">
    <div ref="containerRef" class="display-container">
      <img
        v-if="image?.src"
        ref="imageRef"
        :src="image.src"
        alt="生长识别图片"
        class="display-content"
        @load="measureImage"
      />

      <GrowthDetectionOverlay
        v-if="image?.src && detections.length && hasMeasuredImage"
        :detections="detections"
        :selected-id="selectedId"
        :overlay-bounds="overlayBounds"
        :natural-width="image.width"
        :natural-height="image.height"
        @select="emit('select', $event)"
      />

      <GrowthDetectionState
        :task-status="taskStatus"
        :has-image="Boolean(image?.src)"
        :has-detections="detections.length > 0"
        :message="errorMessage"
      />

      <div v-if="image?.src" class="action-overlay">
        <el-button type="danger" circle size="small" @click="emit('clear')">
          <template #icon>
            <ArtSvgIcon icon="ri:delete-bin-line" />
          </template>
        </el-button>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
  import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import type {
    GrowthDetectionItem,
    GrowthImageMeta,
    GrowthTaskStatus
  } from '@/types/growth-monitoring'
  import GrowthDetectionOverlay from './GrowthDetectionOverlay.vue'
  import GrowthDetectionState from './GrowthDetectionState.vue'

  interface OverlayBounds {
    left: number
    top: number
    width: number
    height: number
  }

  const props = defineProps<{
    image: GrowthImageMeta | null
    detections: GrowthDetectionItem[]
    selectedId: string | null
    taskStatus: GrowthTaskStatus
    errorMessage: string
  }>()

  const emit = defineEmits<{
    select: [id: string]
    clear: []
  }>()

  const containerRef = ref<HTMLDivElement>()
  const imageRef = ref<HTMLImageElement>()
  const overlayBounds = ref<OverlayBounds>({
    left: 0,
    top: 0,
    width: 0,
    height: 0
  })

  let resizeObserver: ResizeObserver | null = null

  const hasMeasuredImage = computed(
    () => overlayBounds.value.width > 0 && overlayBounds.value.height > 0
  )

  const measureImage = () => {
    const container = containerRef.value
    const image = imageRef.value
    if (!container || !image) return

    const containerRect = container.getBoundingClientRect()
    const imageRect = image.getBoundingClientRect()
    overlayBounds.value = {
      left: imageRect.left - containerRect.left,
      top: imageRect.top - containerRect.top,
      width: imageRect.width,
      height: imageRect.height
    }
  }

  onMounted(() => {
    resizeObserver = new ResizeObserver(() => measureImage())
    if (containerRef.value) resizeObserver.observe(containerRef.value)
  })

  onBeforeUnmount(() => {
    resizeObserver?.disconnect()
  })

  watch(
    () => props.image?.src,
    async () => {
      await nextTick()
      measureImage()
    }
  )
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
      overflow: hidden;
      background:
        radial-gradient(circle at top, var(--growth-display-glow) 0%, transparent 32%),
        linear-gradient(
          180deg,
          var(--growth-display-surface-start) 0%,
          var(--growth-display-surface-end) 100%
        );
      border: 1px solid var(--art-card-border);
      border-radius: 16px;
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
      z-index: 5;
      opacity: 0;
      transition: opacity 0.3s ease;
    }

    .display-container:hover .action-overlay {
      opacity: 1;
    }
  }

  :global(html) {
    --growth-display-surface-start: rgb(223 235 248 / 96%);
    --growth-display-surface-end: rgb(232 240 247 / 92%);
    --growth-display-glow: rgb(255 255 255 / 52%);
  }

  :global(html.dark) {
    --growth-display-surface-start: rgb(26 36 52 / 98%);
    --growth-display-surface-end: rgb(17 24 39 / 96%);
    --growth-display-glow: rgb(74 117 170 / 22%);
  }
</style>
