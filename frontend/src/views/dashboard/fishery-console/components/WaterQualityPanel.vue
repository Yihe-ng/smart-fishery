<!-- cspell:ignore echarts tabularnums -->
<template>
  <div class="water-quality-panel">
    <div class="metric-grid">
      <div class="metric-row metric-row-top">
        <article
          v-for="item in topRowItems"
          :key="item.key"
          class="metric-card"
          :class="item.status"
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
              :type="getStatusType(item.status)"
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
            <span class="trend-text">{{ item.deltaText }}</span>
          </div>
        </article>
      </div>

      <div class="metric-row metric-row-bottom">
        <article
          v-for="item in bottomRowItems"
          :key="item.key"
          class="metric-card"
          :class="item.status"
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
              :type="getStatusType(item.status)"
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
            <span class="trend-text">{{ item.deltaText }}</span>
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
  import { computed, nextTick, onMounted, ref, watch } from 'vue'
  import { Loading } from '@element-plus/icons-vue'
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import ArtChart from '@/components/core/charts/art-chart/index.vue'
  import { WATER_QUALITY_THRESHOLDS } from '@/config/thresholds'
  import { WATER_QUALITY_METRICS, getWaterQualityMetricColor } from '@/config/theme'
  import { useChartStyles } from '@/hooks/core/useChart'
  import { getWaterQualityHistory } from '@/api/water-quality'
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
    statusText: string
    deltaText: string
  }

  const TOP_ROW_KEYS: MetricKey[] = ['temperature', 'ammoniaNitrogen', 'ph']
  const BOTTOM_ROW_KEYS: MetricKey[] = ['dissolvedOxygen', 'nitrite']

  const props = defineProps<{
    data: WaterQualityData | null
    previousData?: WaterQualityData | null
    pondId?: string
  }>()

  const { getAxisLineStyle, getAxisLabelStyle, getSplitLineStyle, getTooltipStyle } =
    useChartStyles()

  const dialogVisible = ref(false)
  const chartReady = ref(false)
  const currentMetricKey = ref<MetricKey | null>(null)
  const trendChartRef = ref<InstanceType<typeof ArtChart> | null>(null)
  const historyData = ref<WaterQualityData[]>([])

  const loadHistoryData = async () => {
    try {
      const res = await getWaterQualityHistory({
        pageNum: 1,
        pageSize: 100,
        pondId: props.pondId
      })
      historyData.value = res.list
        .slice()
        .sort((a: WaterQualityData, b: WaterQualityData) => a.collectTime.localeCompare(b.collectTime))
        .slice(-24)
    } catch (err) {
      historyData.value = []
      console.error('Failed to load history data:', err)
    }
  }

  onMounted(() => {
    loadHistoryData()
  })

  watch(
    () => props.pondId,
    () => {
      loadHistoryData()
    }
  )

  const METRIC_DISPLAY_META: Record<MetricKey, { label: string; unit: string }> = {
    temperature: { label: '水温', unit: '℃' },
    ammoniaNitrogen: { label: '氨氮', unit: 'mg/L' },
    ph: { label: 'pH值', unit: '' },
    dissolvedOxygen: { label: '溶解氧', unit: 'mg/L' },
    nitrite: { label: '亚硝酸盐', unit: 'mg/L' }
  }

  const formatMetricNumber = (value: number) => {
    if (Number.isInteger(value)) {
      return value.toString()
    }

    return value.toFixed(value >= 10 ? 1 : 2).replace(/\.?0+$/, '')
  }

  const getMetricStatus = (
    value: number,
    key: keyof typeof WATER_QUALITY_THRESHOLDS
  ): MetricItem['status'] => {
    const rule = WATER_QUALITY_THRESHOLDS[key]
    if (!rule) {
      return 'normal'
    }

    if (rule.max !== undefined && value > rule.max) {
      const overflowRatio = rule.max === 0 ? 0 : (value - rule.max) / rule.max
      return overflowRatio >= 0.2 ? 'danger' : 'warning'
    }

    if (rule.min !== undefined && value < rule.min) {
      const underflowRatio = rule.min === 0 ? 0 : (rule.min - value) / rule.min
      return underflowRatio >= 0.2 ? 'danger' : 'warning'
    }

    return 'normal'
  }

  const getStatusText = (status: MetricItem['status']) => {
    const statusMap = {
      normal: '正常',
      warning: '预警',
      danger: '告警'
    } as const

    return statusMap[status]
  }

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

  const getDeltaText = (key: MetricKey) => {
    const latestValue = props.data?.[key]
    const previousValue = props.previousData?.[key]

    if (typeof latestValue !== 'number' || typeof previousValue !== 'number') {
      return '趋势 --'
    }

    const delta = latestValue - previousValue
    if (Math.abs(delta) < 0.01) {
      return '趋势 持平'
    }

    return `趋势 ${delta > 0 ? '+' : ''}${formatMetricNumber(delta)}`
  }

  const itemMap = computed<Record<MetricKey, MetricItem> | null>(() => {
    if (!props.data) {
      return null
    }

    const currentData = props.data

    return Object.fromEntries(
      Object.keys(METRIC_DISPLAY_META).map((rawKey) => {
        const key = rawKey as MetricKey
        const metric = WATER_QUALITY_METRICS[key]
        const value = currentData[key] as number
        const status = getMetricStatus(value, key)
        const displayMeta = METRIC_DISPLAY_META[key]

        const item: MetricItem = {
          key,
          label: displayMeta.label,
          value,
          unit: displayMeta.unit,
          icon: metric.icon,
          color: getWaterQualityMetricColor(key),
          status,
          statusText: getStatusText(status),
          deltaText: getDeltaText(key)
        }

        return [key, item]
      })
    ) as Record<MetricKey, MetricItem>
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

  const currentItem = computed<MetricItem | null>(() => {
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
