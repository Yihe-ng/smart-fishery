<!-- cspell:ignore echarts tabularnums -->
<template>
  <div class="water-quality-panel">
    <div class="metric-grid">
      <div class="metric-row metric-row-top">
        <article
          v-for="item in topRowItems"
          :key="item.key"
          class="metric-card"
          :class="item.statusClass"
          :style="{ '--metric-accent': item.color }"
          @click="handleCardClick(item)"
        >
          <div class="metric-head">
            <div class="metric-title">
              <div class="icon-box">
                <ArtSvgIcon :icon="item.icon" />
              </div>
              <span class="label">{{ item.label }}</span>
            </div>
            <el-tag
              :type="getStatusType(item.statusText)"
              size="small"
              effect="light"
              class="status-tag"
            >
              {{ item.statusText }}
            </el-tag>
          </div>

          <div class="metric-main">
            <span class="value">{{ formatMetricNumber(item.value) }}</span>
            <span v-if="item.unit" class="unit">{{ item.unit }}</span>
          </div>

          <div class="metric-meta metric-meta-inline">
            <span class="trend-text">{{ item.trendText }}</span>
          </div>
        </article>
      </div>

      <div class="metric-row metric-row-bottom">
        <article
          v-for="item in bottomRowItems"
          :key="item.key"
          class="metric-card"
          :class="item.statusClass"
          :style="{ '--metric-accent': item.color }"
          @click="handleCardClick(item)"
        >
          <div class="metric-head">
            <div class="metric-title">
              <div class="icon-box">
                <ArtSvgIcon :icon="item.icon" />
              </div>
              <span class="label">{{ item.label }}</span>
            </div>
            <el-tag
              :type="getStatusType(item.statusText)"
              size="small"
              effect="light"
              class="status-tag"
            >
              {{ item.statusText }}
            </el-tag>
          </div>

          <div class="metric-main">
            <span class="value">{{ formatMetricNumber(item.value) }}</span>
            <span v-if="item.unit" class="unit">{{ item.unit }}</span>
          </div>

          <div class="metric-meta metric-meta-inline">
            <span class="trend-text">{{ item.trendText }}</span>
          </div>
        </article>
      </div>
    </div>

    <el-dialog
      v-model="dialogVisible"
      :title="currentItem ? `${currentItem.label} 24小时趋势` : '24小时趋势'"
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
  import { computed, nextTick, onMounted, ref } from 'vue'
  import { Loading } from '@element-plus/icons-vue'

  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import ArtChart from '@/components/core/charts/art-chart/index.vue'
  import { WATER_QUALITY_METRICS, getWaterQualityMetricColor } from '@/config/theme'
  import { useChartStyles } from '@/hooks/core/useChart'
  import { getWaterQualityHistory } from '@/api/water-quality'
  import type { EChartsOption } from '@/plugins/echarts'
  import type { DashboardFrameMetric, WaterQualityData } from '@/types/water-quality'
  import type { WaterQualityMetricKey } from '@/config/theme'

  interface MetricCardItem extends DashboardFrameMetric {
    icon: string
    color: string
    statusClass: 'normal' | 'warning' | 'danger'
  }

  const TOP_ROW_KEYS: WaterQualityMetricKey[] = ['temperature', 'ammoniaNitrogen', 'ph']
  const BOTTOM_ROW_KEYS: WaterQualityMetricKey[] = ['dissolvedOxygen', 'nitrite']

  const props = defineProps<{
    metrics: Record<WaterQualityMetricKey, DashboardFrameMetric> | null
  }>()

  const { getAxisLineStyle, getAxisLabelStyle, getSplitLineStyle, getTooltipStyle } =
    useChartStyles()

  const dialogVisible = ref(false)
  const chartReady = ref(false)
  const currentMetricKey = ref<WaterQualityMetricKey | null>(null)
  const trendChartRef = ref<InstanceType<typeof ArtChart> | null>(null)
  const historyData = ref<WaterQualityData[]>([])

  const loadHistoryData = async () => {
    try {
      const res = await getWaterQualityHistory({
        pageNum: 1,
        pageSize: 100
      })
      historyData.value = res.list
        .slice()
        .sort((a, b) => a.collectTime.localeCompare(b.collectTime))
        .slice(-24)
    } catch (err) {
      historyData.value = []
      console.error('Failed to load history data:', err)
    }
  }

  onMounted(() => {
    loadHistoryData()
  })

  const formatMetricNumber = (value: number) => {
    if (Number.isInteger(value)) {
      return value.toString()
    }

    return value.toFixed(value >= 10 ? 1 : 2).replace(/\.?0+$/, '')
  }

  const getStatusType = (
    statusText: DashboardFrameMetric['statusText']
  ): 'success' | 'warning' | 'danger' | 'info' => {
    const statusMap = {
      正常: 'success',
      警戒: 'warning',
      危险: 'danger'
    } as const

    return statusMap[statusText] ?? 'info'
  }

  const getStatusClass = (statusText: DashboardFrameMetric['statusText']) => {
    const statusMap = {
      正常: 'normal',
      警戒: 'warning',
      危险: 'danger'
    } as const

    return statusMap[statusText]
  }

  const itemMap = computed<Record<WaterQualityMetricKey, MetricCardItem> | null>(() => {
    if (!props.metrics) {
      return null
    }

    return Object.fromEntries(
      Object.entries(props.metrics).map(([rawKey, item]) => {
        const key = rawKey as WaterQualityMetricKey
        const metric = WATER_QUALITY_METRICS[key]
        return [
          key,
          {
            ...item,
            icon: metric.icon,
            color: getWaterQualityMetricColor(key),
            statusClass: getStatusClass(item.statusText)
          }
        ]
      })
    ) as Record<WaterQualityMetricKey, MetricCardItem>
  })

  const topRowItems = computed(() => {
    if (!itemMap.value) {
      return []
    }

    return TOP_ROW_KEYS.map((key) => itemMap.value![key])
  })

  const bottomRowItems = computed(() => {
    if (!itemMap.value) {
      return []
    }

    return BOTTOM_ROW_KEYS.map((key) => itemMap.value![key])
  })

  const currentItem = computed<MetricCardItem | null>(() => {
    if (!currentMetricKey.value || !itemMap.value) {
      return null
    }

    return itemMap.value[currentMetricKey.value] ?? null
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

  const handleCardClick = (item: MetricCardItem) => {
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
    height: 100%;
    min-height: 0;
    box-sizing: border-box;
    padding-bottom: 10px;

    .metric-grid {
      display: flex;
      height: 100%;
      min-height: 0;
      flex-direction: column;
      gap: 8px;
    }

    .metric-row {
      display: grid;
      width: 100%;
      min-height: 0;
      gap: 12px;
      align-items: start;
    }

    .metric-row-top {
      flex: 1 1 0;
      min-height: 0;
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }

    .metric-row-bottom {
      flex: 1 1 0;
      min-height: 0;
      width: 96%;
      margin-inline: auto;
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .metric-card {
      display: grid;
      height: 100%;
      min-height: 0;
      grid-template-rows: auto auto auto;
      align-content: center;
      row-gap: 8px;
      min-width: 0;
      padding: 12px 12px;
      cursor: pointer;
      background: var(--metric-card-bg, var(--default-box-color));
      border: 1px solid var(--art-card-border);
      border-left: 4px solid var(--metric-accent, var(--el-color-primary));
      border-radius: 12px;
      box-shadow: 0 2px 8px rgb(15 23 42 / 6%);
      transition:
        border-color 0.25s ease,
        box-shadow 0.25s ease,
        transform 0.25s ease,
        background-color 0.25s ease;

      &:hover {
        background: var(--metric-card-hover-bg, var(--metric-card-bg, var(--default-box-color)));
        box-shadow: 0 12px 28px rgb(15 23 42 / 14%);
        transform: translateY(-1px);
      }
    }

    .metric-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
    }

    .metric-title {
      display: flex;
      min-width: 0;
      flex: 1;
      align-items: center;
      gap: 8px;
      overflow: hidden;
    }

    .icon-box {
      display: flex;
      width: 30px;
      height: 30px;
      flex-shrink: 0;
      align-items: center;
      justify-content: center;
      font-size: 15px;
      color: var(--metric-accent);
      background-color: color-mix(in oklch, var(--metric-accent) 14%, transparent);
      border-radius: 8px;
    }

    .label {
      min-width: 0;
      overflow: hidden;
      font-size: 15px;
      font-weight: 700;
      line-height: 1.2;
      color: var(--el-text-color-primary);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .status-tag {
      flex-shrink: 0;
      margin-top: 2px;
      font-size: 9px;
      font-weight: 600;
      letter-spacing: 0;
      opacity: 0.9;
    }

    .metric-main {
      display: flex;
      align-items: baseline;
      gap: 4px;
      line-height: 1;
    }

    .value {
      font-size: 30px;
      font-weight: 800;
      line-height: 1;
      letter-spacing: -0.03em;
      color: var(--el-text-color-primary);
      font-variant-numeric: tabular-nums;
    }

    .unit {
      font-size: 11px;
      font-weight: 600;
      line-height: 1;
      color: var(--el-text-color-secondary);
    }

    .metric-meta {
      min-width: 0;
    }

    .metric-meta-inline {
      display: flex;
      min-height: 20px;
      align-items: center;
      justify-content: flex-start;
      width: fit-content;
      max-width: 100%;
    }

    .trend-text {
      display: inline-flex;
      min-height: 18px;
      align-items: center;
      justify-content: center;
      min-width: 64px;
      padding: 0 7px;
      font-size: 10px;
      font-weight: 700;
      line-height: 1;
      color: var(--metric-accent);
      white-space: nowrap;
      background-color: color-mix(in oklch, var(--metric-accent) 10%, transparent);
      border-radius: 999px;
      font-variant-numeric: tabular-nums;
    }

    :deep(.el-tag.status-tag) {
      height: 18px;
      padding: 0 5px;
      border-color: color-mix(in oklch, currentColor 14%, transparent);
      background-color: color-mix(in oklch, currentColor 7%, transparent);
    }
  }

  :global(.dark) .water-quality-panel {
    --metric-card-bg: var(--art-nested-card-bg);
    --metric-card-hover-bg: var(--art-nested-card-hover);
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

    .trend-text {
      background-color: color-mix(in oklch, var(--metric-accent) 16%, transparent);
    }

    :deep(.el-tag.status-tag) {
      background-color: color-mix(in oklch, currentColor 10%, transparent);
      border-color: color-mix(in oklch, currentColor 18%, transparent);
    }
  }
</style>
