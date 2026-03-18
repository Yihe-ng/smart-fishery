<template>
  <span class="art-ai-icon" :class="sizeClass" aria-hidden="true">
    <ArtSvgIcon icon="ri:message-ai-3-line" class="icon" />
  </span>
</template>

<script setup lang="ts">
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'

  defineOptions({ name: 'ArtAiIcon' })

  interface Props {
    size?: 'sm' | 'md'
  }

  const props = withDefaults(defineProps<Props>(), {
    size: 'md'
  })

  const sizeClass = computed(() => `size-${props.size}`)
</script>

<style scoped lang="scss">
  .art-ai-icon {
    --icon-size: 16px;
    --icon-color: color-mix(in srgb, var(--el-text-color-primary) 78%, var(--el-color-primary) 22%);
    position: relative;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: var(--icon-size);
    height: var(--icon-size);
    box-sizing: border-box;
  }

  .art-ai-icon.size-sm {
    --icon-size: 14px;
  }

  .art-ai-icon.size-md {
    --icon-size: 16px;
  }

  .icon {
    font-size: calc(var(--icon-size) + 2px);
    color: var(--icon-color);
  }

  :global(.dark) .art-ai-icon {
    --icon-color: color-mix(in srgb, #dbeafe 82%, #60a5fa 18%);
  }
</style>
