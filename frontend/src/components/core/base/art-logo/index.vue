<!-- 系统logo -->
<template>
  <div class="flex-cc" :style="logoStyle">
    <!-- 使用石斑鱼 SVG 作为系统 Logo -->
    <img
      src="@/assets/images/svg/石斑鱼 (蓝色).svg"
      alt="logo"
      class="w-full h-full object-contain flip-x"
    />
  </div>
</template>

<script setup lang="ts">
  defineOptions({ name: 'ArtLogo' })

  interface Props {
    /** logo 大小 */
    size?: number | string
  }

  const props = withDefaults(defineProps<Props>(), {
    size: 36
  })

  const logoStyle = computed(() => ({
    width: `${props.size}px`,
    height: `${props.size}px`
  }))
</script>
h
<style scoped>
  .flip-x {
    transform: scaleX(-1);
  }
</style>
