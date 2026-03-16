<!-- cspell:ignore echarts tabularnums -->
<template>
  <div class="water-quality-panel">
    <el-row :gutter="12">
      <el-col
        v-for="item in items"
        :key="item.key"
        :xs="12"
        :sm="12"
        :md="8"
        :lg="4.8"
        class="mb-3"
      >
        <el-card
          shadow="never"
          class="metric-card"
          :style="{ '--metric-accent': item.color }"
          @click="handleCardClick(item)"
        >
          <div class="metric-head flex-cb">
            <div class="flex-c gap-2">
              <div class="icon-box">
                <ArtSvgIcon :icon="item.icon" />
              </div>
              <span class="label">{{ item.label }}</span>
            </div>
            <el-tag
              :type="getStatusType(item.status)"
              size="small"
              effect="light"
              class="status-tag"
            >
              {{ getStatusText(item.status) }}
            </el-tag>
          </div>

          <div class="metric-main mt-3 flex-baseline gap-1">
            <span class="value">{{ item.value }}</span>
            <span class="unit">{{ item.unit }}</span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog
      v-model="dialogVisible"
      :title="currentItem ? `${currentItem.label} 24 小时趋势` : '24 小时趋势'"
      width="700px"
      append-to-body
      @opened="handleDialogOpened"
      @closed="handleDialogClosed"
    >
      <div class="h-80 w-full">
        <div v-if="!chartReady" class="flex h-full items-center justify-center">
          <el-icon class="is-loading" :size="32">
            <Loading />
          </el-icon>
        </div>
        <ArtChart
          v-if="chartReady && currentItem"
          ref="trendChartRef"
          :key="currentMetricKey ?? undefined"
          :option="chartOption"
          height="320px"
        />
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
  import { computed, nextTick, ref } from 'vue'
  import { Loading } from '@element-plus/icons-vue'
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import ArtChart from '@/components/core/charts/art-chart/index.vue'
  import { WATER_QUALITY_THRESHOLDS } from '@/config/thresholds'
  import {
    WATER_QUALITY_METRIC_ORDER,
    WATER_QUALITY_METRICS,
    getWaterQualityMetricColor
  } from '@/config/theme'
  import { useChartStyles } from '@/hooks/core/useChart'
  import waterQualityMockData from '@/mock/water-quality-data.json'
  import type { EChartsOption } from '@/plugins/echarts'
  import type { WaterQualityData } from '@/types/water-quality'

  type MetricKey = keyof WaterQualityData & keyof typeof WATER_QUALITY_METRICS

  interface MetricItem {
    key: MetricKey
    label: string
    value: number
    unit: string
    icon: string
    color: string
    status: 'normal' | 'warning' | 'danger'
  }

  const props = defineProps<{
    data: WaterQualityData | null
  }>()

  const { getAxisLineStyle, getAxisLabelStyle, getSplitLineStyle, getTooltipStyle } =
    useChartStyles()

  const dialogVisible = ref(false)
  const chartReady = ref(false)
  const currentMetricKey = ref<MetricKey | null>(null)
  const trendChartRef = ref<InstanceType<typeof ArtChart> | null>(null)

  const items = computed<MetricItem[]>(() => {
    if (!props.data) {
      return []
    }

    const getStatus = (value: number, key: keyof typeof WATER_QUALITY_THRESHOLDS) => {
      const rule = WATER_QUALITY_THRESHOLDS[key]
      if (!rule) {
        return 'normal'
      }

      if (
        (rule.max !== undefined && value > rule.max) ||
        (rule.min !== undefined && value < rule.min)
      ) {
        return 'warning'
      }

      return 'normal'
    }

    return WATER_QUALITY_METRIC_ORDER.map((key) => {
      const metric = WATER_QUALITY_METRICS[key]

      return {
        key,
        label: metric.label,
        value: props.data?.[key] as number,
        unit: metric.unit,
        icon: metric.icon,
        color: getWaterQualityMetricColor(key),
        status: getStatus(props.data?.[key] as number, key)
      }
    })
  })

  const currentItem = computed<MetricItem | null>(() => {
    if (!props.data || !currentMetricKey.value) {
      return null
    }

    return items.value.find((item) => item.key === currentMetricKey.value) ?? null
  })

  const historyData = computed(() => {
    return [...(waterQualityMockData as unknown as WaterQualityData[])]
      .sort((a, b) => a.collectTime.localeCompare(b.collectTime))
      .slice(-24)
  })

  const chartOption = computed<EChartsOption>(() => {
    const item = currentItem.value

    if (!item) {
      return {}
    }

    const dates = historyData.value.map(
      (historyItem) => historyItem.collectTime.split(' ')[1] || historyItem.collectTime
    )
    const values = historyData.value.map((historyItem) => historyItem[item.key] as number)

    return {
      tooltip: getTooltipStyle('axis', {
        triggerOn: 'mousemove|click',
        axisPointer: {
          type: 'line',
          snap: true,
          animation: false
        },
        formatter: `{b}<br />${item.label}: {c}${item.unit}`
      }),
      grid: {
        top: '10%',
        left: '3%',
        right: '4%',
        bottom: '15%',
        containLabel: true
      },
      dataZoom: [
        {
          type: 'inside',
          start: 0,
          end: 100,
          zoomOnMouseWheel: false,
          moveOnMouseWheel: true
        },
        {
          start: 0,
          end: 100
        }
      ],
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: dates,
        axisLine: getAxisLineStyle().lineStyle,
        axisLabel: getAxisLabelStyle()
      },
      yAxis: {
        type: 'value',
        axisLine: getAxisLineStyle().lineStyle,
        axisLabel: getAxisLabelStyle(),
        splitLine: getSplitLineStyle().lineStyle
      },
      series: [
        {
          name: item.label,
          type: 'line',
          smooth: true,
          showSymbol: false,
          emphasis: {
            focus: 'none'
          },
          data: values,
          itemStyle: { color: item.color },
          lineStyle: { color: item.color },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: item.color },
                { offset: 1, color: 'rgba(255, 255, 255, 0)' }
              ]
            },
            opacity: 0.28
          }
        }
      ]
    }
  })

  const getStatusType = (
    status: MetricItem['status']
  ): 'success' | 'warning' | 'danger' | 'info' => {
    const statusMap = {
      normal: 'success',
      warning: 'warning',
      danger: 'danger'
    } as const

    return statusMap[status] ?? 'info'
  }

  const getStatusText = (status: MetricItem['status']) => {
    const statusMap = {
      normal: '正常',
      warning: '预警',
      danger: '告警'
    } as const

    return statusMap[status] ?? '未知'
  }

  const handleCardClick = (item: MetricItem) => {
    currentMetricKey.value = item.key
    dialogVisible.value = true
  }

  const handleDialogOpened = async () => {
    await nextTick()
    chartReady.value = true
    await nextTick()
    trendChartRef.value?.resize()
  }

  const handleDialogClosed = () => {
    chartReady.value = false
    currentMetricKey.value = null
  }
</script>

<style scoped lang="scss">
  .water-quality-panel {
    .metric-card {
      cursor: pointer;
      border: 1px solid var(--art-card-border);
      border-left: 4px solid var(--metric-accent, var(--el-color-primary));
      border-radius: 12px;
      box-shadow: 0 2px 8px rgb(15 23 42 / 6%);
      transition:
        border-color 0.25s ease,
        box-shadow 0.25s ease,
        transform 0.25s ease;

      :deep(.el-card__body) {
        padding: 16px;
      }

      &:hover {
        box-shadow: 0 12px 28px rgb(15 23 42 / 14%);
        transform: translateY(-3px) scale(1.02);
      }
    }

    .metric-head {
      min-height: 26px;
    }

    .icon-box {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 32px;
      height: 32px;
      font-size: 18px;
      color: var(--metric-accent);
      background-color: color-mix(in oklch, var(--metric-accent) 16%, transparent);
      border-radius: 8px;
    }

    .label {
      font-size: 14px;
      font-weight: 500;
      line-height: 1.4;
      color: var(--el-text-color-regular);
    }

    .status-tag {
      font-size: 11px;
      font-weight: 600;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }

    .metric-main {
      align-items: baseline;
      margin-top: 14px;
      line-height: 1;
    }

    .value {
      font-size: 28px;
      font-weight: 700;
      line-height: 1;
      letter-spacing: -0.02em;
      color: var(--el-text-color-primary);
      font-variant-numeric: tabular-nums;
    }

    .unit {
      font-size: 12px;
      font-weight: 500;
      line-height: 1;
      letter-spacing: 0.02em;
      color: var(--el-text-color-secondary);
      text-transform: uppercase;
    }

    :deep(.el-tag.status-tag) {
      padding: 0 7px;
    }
  }

  :global(.dark) .water-quality-panel .metric-card {
    border-color: color-mix(in oklch, var(--metric-accent) 20%, transparent);
    box-shadow:
      0 2px 8px rgb(0 0 0 / 30%),
      inset 0 1px 0 color-mix(in oklch, var(--metric-accent) 8%, transparent);

    &:hover {
      box-shadow:
        0 12px 28px rgb(0 0 0 / 40%),
        0 0 0 1px color-mix(in oklch, var(--metric-accent) 35%, transparent);
    }

    .icon-box {
      color: color-mix(in oklch, var(--metric-accent) 72%, var(--el-text-color-primary));
      background-color: color-mix(in oklch, var(--metric-accent) 20%, transparent);
    }
  }
</style>
