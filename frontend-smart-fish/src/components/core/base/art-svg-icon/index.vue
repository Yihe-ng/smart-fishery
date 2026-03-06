<!-- 图标组件 -->
<template>
  <Icon v-if="icon" :icon="icon" v-bind="bindAttrs" class="art-svg-icon inline" />
</template>

<script setup lang="ts">
  import { Icon } from '@iconify/vue'

  defineOptions({ name: 'ArtSvgIcon', inheritAttrs: false })

  interface Props {
    /** Iconify icon name */
    icon?: string
    /** 图标大小 */
    size?: number | string
  }

  const props = defineProps<Props>()

  const attrs = useAttrs()

  const bindAttrs = computed(() => {
    const { class: className, style, ...rest } = attrs
    const sizeStyle = props.size
      ? { fontSize: `${props.size}px`, width: `${props.size}px`, height: `${props.size}px` }
      : {}

    return {
      class: (className as string) || '',
      style: [(style as string) || '', sizeStyle],
      ...rest
    }
  })
</script>
