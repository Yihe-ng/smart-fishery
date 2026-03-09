<template>
  <div class="art-chart-container relative" :style="{ height, width }">
    <!-- 空状态 -->
    <div
      v-if="isEmpty"
      class="absolute inset-0 z-10 flex flex-col items-center justify-center bg-[var(--el-bg-color)]"
    >
      <el-empty :description="emptyText" />
    </div>

    <!-- 加载状态 -->
    <div
      v-if="loading"
      class="absolute inset-0 z-20 flex items-center justify-center bg-[var(--el-bg-color-overlay)] opacity-80"
      v-loading="loading"
    ></div>

    <!-- 图表 -->
    <v-chart
      ref="chartRef"
      class="chart-instance"
      :option="option"
      :theme="theme"
      :init-options="{ renderer: props.renderer }"
      :manual-update="false"
      autoresize
      v-bind="$attrs"
      @click="handleClick"
    />
  </div>
</template>

<script setup lang="ts">
  import { computed, ref, watch } from 'vue'
  import { useSettingStore } from '@/store/modules/setting'
  import type { EChartsOption } from '@/plugins/echarts'

  defineOptions({ name: 'ArtChart' })

  interface Props {
    /** ECharts 配置项 */
    option: EChartsOption
    /** 容器宽度 */
    width?: string
    /** 容器高度 */
    height?: string
    /** 加载状态 */
    loading?: boolean
    /** 是否为空数据 */
    isEmpty?: boolean
    /** 空数据提示文案 */
    emptyText?: string
    /** 渲染器类型: 'canvas' | 'svg' */
    renderer?: 'canvas' | 'svg'
  }

  const props = withDefaults(defineProps<Props>(), {
    width: '100%',
    height: '100%',
    loading: false,
    isEmpty: false,
    emptyText: '暂无数据',
    renderer: 'canvas'
  })

  const emit = defineEmits(['click'])

  const settingStore = useSettingStore()
  const chartRef = ref<any>(null)

  // 主题计算
  const theme = computed(() => (settingStore.isDark ? 'dark' : ''))

  // 监听菜单展开收起，触发重绘
  // 虽然 autoresize 能处理大部分情况，但菜单动画可能导致 ResizeObserver 延迟触发或不平滑
  // 这里保留原有的优化逻辑，在菜单状态变化后强制刷新一次
  watch(
    () => settingStore.menuOpen,
    () => {
      setTimeout(() => {
        chartRef.value?.resize()
      }, 300)
    }
  )

  const handleClick = (params: any) => {
    emit('click', params)
  }

  // 暴露 resize 方法供外部调用
  const resize = () => {
    chartRef.value?.resize()
  }

  defineExpose({
    resize,
    chartRef
  })
</script>

<style scoped>
  .art-chart-container {
    overflow: hidden;
  }

  .chart-instance {
    width: 100%;
    height: 100%;
  }
</style>
