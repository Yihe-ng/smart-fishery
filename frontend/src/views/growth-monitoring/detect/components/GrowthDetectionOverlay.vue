<template>
  <div class="growth-detection-overlay">
    <svg
      class="mask-svg"
      viewBox="0 0 1 1"
      preserveAspectRatio="none"
      :style="svgStyle"
    >
      <polygon
        v-for="item in maskItems"
        :key="item.id"
        class="mask-polygon"
        :class="{ active: item.id === selectedId }"
        :points="item.points"
        @click="emit('select', item.id)"
      />
      <rect
        v-for="item in fallbackBboxItems"
        :key="item.id"
        class="mask-fallback-rect"
        :class="{ active: item.id === selectedId }"
        :x="item.x"
        :y="item.y"
        :width="item.width"
        :height="item.height"
        rx="0.004"
        @click="emit('select', item.id)"
      />
    </svg>

    <button
      v-for="item in labelBoxes"
      :key="item.id"
      type="button"
      class="detection-label"
      :class="{ active: item.id === selectedId }"
      :style="item.style"
      @click="emit('select', item.id)"
    >
      <span class="box-label">{{ item.labelText }}</span>
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

  const svgStyle = computed<CSSProperties>(() => {
    const { left, top, width, height } = props.overlayBounds
    if (width <= 0 || height <= 0) {
      return { display: 'none' }
    }
    return {
      position: 'absolute',
      left: `${left}px`,
      top: `${top}px`,
      width: `${width}px`,
      height: `${height}px`,
    }
  })

  const maskIds = computed(() => {
    const set = new Set<string>()
    props.detections
      .filter((d) => d.maskPolygons?.length)
      .forEach((d) => {
        set.add(d.id)
      })
    return set
  })

  const maskItems = computed(() =>
    props.detections
      .filter((d) => d.maskPolygons?.length)
      .map((d) => ({
        id: d.id,
        points: d.maskPolygons.map((pt) => `${pt[0]},${pt[1]}`).join(' '),
      }))
  )

  const fallbackBboxItems = computed(() => {
    if (!props.naturalWidth || !props.naturalHeight) return []
    const nw = props.naturalWidth
    const nh = props.naturalHeight

    return props.detections
      .filter((d) => !maskIds.value.has(d.id))
      .map((d) => ({
        id: d.id,
        x: d.bbox.x / nw,
        y: d.bbox.y / nh,
        width: d.bbox.width / nw,
        height: d.bbox.height / nh,
      }))
  })

  const labelBoxes = computed(() => {
    if (!props.naturalWidth || !props.naturalHeight) return []

    const scaleX = props.overlayBounds.width / props.naturalWidth
    const scaleY = props.overlayBounds.height / props.naturalHeight
    const containerW = props.overlayBounds.width

    return props.detections.map((detection) => {
      const bboxLeft = detection.bbox.x * scaleX
      const bboxRight = (detection.bbox.x + detection.bbox.width) * scaleX
      const labelEstimateW = 130

      const nearRight = props.overlayBounds.left + bboxRight + labelEstimateW > props.overlayBounds.left + containerW

      const style: CSSProperties = {
        left: `${props.overlayBounds.left + (nearRight ? bboxRight : bboxLeft)}px`,
        top: `${props.overlayBounds.top + detection.bbox.y * scaleY}px`,
        transform: nearRight ? 'translateX(-100%)' : undefined,
      }

      return {
        id: detection.id,
        labelText: detection.labelText,
        style,
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

  .mask-svg {
    pointer-events: none;

    polygon,
    rect {
      pointer-events: auto;
    }
  }

  .mask-polygon {
    fill: transparent;
    stroke: #1677ff;
    stroke-width: 0.003;
    stroke-linejoin: round;
    cursor: pointer;
    transition:
      stroke 0.2s ease,
      fill 0.2s ease,
      stroke-width 0.2s ease;
  }

  .mask-polygon:hover {
    stroke: #4096ff;
    fill: rgb(22 119 255 / 8%);
    stroke-width: 0.004;
  }

  .mask-polygon.active {
    stroke: #36cfc9;
    fill: rgb(54 207 201 / 20%);
    stroke-width: 0.005;
  }

  .mask-fallback-rect {
    fill: transparent;
    stroke: #1677ff;
    stroke-width: 0.002;
    stroke-dasharray: 0.006 0.004;
    stroke-opacity: 0.5;
    cursor: pointer;
    transition:
      stroke 0.2s ease,
      stroke-opacity 0.2s ease;
  }

  .mask-fallback-rect:hover {
    stroke: #4096ff;
    stroke-opacity: 0.8;
  }

  .mask-fallback-rect.active {
    stroke: #36cfc9;
    stroke-opacity: 1;
    stroke-dasharray: none;
    stroke-width: 0.003;
  }

  .detection-label {
    position: absolute;
    display: block;
    width: 0;
    height: 0;
    padding: 0;
    pointer-events: auto;
    background: transparent;
    border: none;
    outline: none;
    cursor: pointer;
  }

  .box-label {
    display: block;
    min-width: max-content;
    max-width: 220px;
    padding: 4px 8px;
    margin: 2px 0 0 2px;
    overflow: hidden;
    font-size: 11px;
    font-weight: 600;
    color: #fff;
    line-height: 1.3;
    text-shadow: 0 1px 2px rgb(0 0 0 / 30%);
    white-space: nowrap;
    background: linear-gradient(135deg, #1677ff 0%, #36cfc9 100%);
    border-radius: 4px;
    opacity: 0.82;
    transition: opacity 0.2s ease;
  }

  .detection-label:hover .box-label,
  .detection-label.active .box-label {
    opacity: 1;
  }

  .detection-label.active .box-label {
    background: linear-gradient(135deg, #13c2c2 0%, #08979c 100%);
  }
</style>
