<template>
  <div class="growth-detection-overlay">
    <button
      v-for="item in boxes"
      :key="item.id"
      type="button"
      class="detection-box"
      :class="{ active: item.id === selectedId }"
      :style="item.style"
      @click="emit('select', item.id)"
    >
      <span class="box-label">
        {{ item.labelText }}
      </span>
    </button>
  </div>
</template>

<script setup lang="ts">
  import { computed } from 'vue'
  import type { CSSProperties } from 'vue'
  import type { GrowthDetectionItem } from '@/types/growth-monitoring'

  interface OverlayBounds {
    left: number
    top: number
    width: number
    height: number
  }

  const props = defineProps<{
    detections: GrowthDetectionItem[]
    selectedId: string | null
    overlayBounds: OverlayBounds
    naturalWidth: number
    naturalHeight: number
  }>()

  const emit = defineEmits<{
    select: [id: string]
  }>()

  const boxes = computed(() => {
    if (!props.naturalWidth || !props.naturalHeight) return []

    const scaleX = props.overlayBounds.width / props.naturalWidth
    const scaleY = props.overlayBounds.height / props.naturalHeight

    return props.detections.map((detection) => {
      const style: CSSProperties = {
        left: `${props.overlayBounds.left + detection.bbox.x * scaleX}px`,
        top: `${props.overlayBounds.top + detection.bbox.y * scaleY}px`,
        width: `${detection.bbox.width * scaleX}px`,
        height: `${detection.bbox.height * scaleY}px`
      }

      return {
        id: detection.id,
        labelText: detection.labelText,
        style
      }
    })
  })
</script>

<style scoped lang="scss">
  .growth-detection-overlay {
    position: absolute;
    inset: 0;
    z-index: 3;
    pointer-events: none;
  }

  .detection-box {
    position: absolute;
    display: flex;
    align-items: flex-start;
    justify-content: flex-start;
    pointer-events: auto;
    background: transparent;
    border: 2px solid rgb(22 119 255 / 55%);
    border-radius: 12px;
    box-shadow: 0 0 0 1px rgb(255 255 255 / 18%);
    transition:
      border-color 0.2s ease,
      box-shadow 0.2s ease,
      transform 0.2s ease,
      opacity 0.2s ease;
    opacity: 0.68;
  }

  .detection-box:hover,
  .detection-box.active {
    border-color: #36cfc9;
    box-shadow:
      0 0 0 2px rgb(54 207 201 / 22%),
      0 10px 30px rgb(0 0 0 / 18%);
    opacity: 1;
    transform: translateY(-1px);
  }

  .box-label {
    max-width: min(220px, 100%);
    padding: 6px 10px;
    margin: -1px 0 0 -1px;
    overflow: hidden;
    font-size: 12px;
    font-weight: 600;
    color: #fff;
    text-overflow: ellipsis;
    white-space: nowrap;
    background: linear-gradient(135deg, #1677ff 0%, #36cfc9 100%);
    border-top-left-radius: 10px;
    border-bottom-right-radius: 10px;
  }

  .detection-box.active .box-label {
    background: linear-gradient(135deg, #13c2c2 0%, #08979c 100%);
  }
</style>
