<!-- 柱状图卡片 -->
<template>
  <div class="art-card relative overflow-hidden" :style="{ height: `${height}rem` }">
    <div class="mb-5 flex-b items-start px-5 pt-5">
      <div>
        <p class="m-0 text-2xl font-medium leading-tight text-g-900">
          {{ value }}
        </p>
        <p class="mt-1 text-sm text-g-600">{{ label }}</p>
      </div>
      <div
        class="text-sm font-medium text-danger"
        :class="[percentage > 0 ? 'text-success' : '', isMiniChart ? 'absolute bottom-5' : '']"
      >
        {{ percentage > 0 ? '+' : '' }}{{ percentage }}%
      </div>
      <div v-if="date" class="absolute bottom-5 right-5 text-xs text-g-600">
        {{ date }}
      </div>
    </div>
    <div
      class="absolute bottom-0 left-0 right-0 mx-auto"
      :class="isMiniChart ? '!absolute !top-5 !right-5 !bottom-auto !left-auto !h-15 !w-4/10' : ''"
      :style="{ height: isMiniChart ? '60px' : `calc(${height}rem - 5rem)` }"
    >
      <ArtChart :option="chartOption" :is-empty="isEmpty" />
    </div>
  </div>
</template>

<script setup lang="ts">
  import { computed } from 'vue'
  import { useChartOps } from '@/hooks/core/useChart'
  import { type EChartsOption } from '@/plugins/echarts'
  import ArtChart from '@/components/core/charts/art-chart/index.vue'

  defineOptions({ name: 'ArtBarChartCard' })

  interface Props {
    /** 数值 */
    value: number
    /** 标签 */
    label: string
    /** 百分比 +（绿色）-（红色） */
    percentage: number
    /** 日期 */
    date?: string
    /** 高度 */
    height?: number
    /** 颜色 */
    color?: string
    /** 图表数据 */
    chartData: number[]
    /** 柱状图宽度 */
    barWidth?: string
    /** 是否为迷你图表 */
    isMiniChart?: boolean
  }

  const props = withDefaults(defineProps<Props>(), {
    height: 11,
    barWidth: '26%'
  })

  // 检查是否为空数据
  const isEmpty = computed(
    () => !props.chartData?.length || props.chartData.every((val) => val === 0)
  )

  // 生成图表配置
  const chartOption = computed<EChartsOption>(() => {
    const computedColor = props.color || useChartOps().themeColor

    return {
      grid: {
        top: 0,
        right: 0,
        bottom: 15,
        left: 0
      },
      xAxis: {
        type: 'category',
        show: false
      },
      yAxis: {
        type: 'value',
        show: false
      },
      series: [
        {
          data: props.chartData,
          type: 'bar',
          barWidth: props.barWidth,
          itemStyle: {
            color: computedColor,
            borderRadius: 2
          }
        }
      ]
    }
  })
</script>
