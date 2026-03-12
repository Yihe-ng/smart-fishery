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
          <div class="flex-cb metric-head">
            <div class="flex-c gap-2">
              <div class="icon-box" :style="iconBoxStyle(item.color)">
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
          <div class="mt-3 flex-baseline gap-1 metric-main">
            <span class="value">{{ item.value }}</span>
            <span class="unit">{{ item.unit }}</span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 趋势详情弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="currentItem?.label + ' 24小时趋势'"
      width="700px"
      append-to-body
      @opened="handleDialogOpened"
      @closed="handleDialogClosed"
    >
      <div class="h-80 w-full">
        <!-- 图表加载中占位 -->
        <div v-if="!chartReady" class="flex items-center justify-center h-full">
          <el-icon class="is-loading" :size="32">
            <Loading />
          </el-icon>
        </div>
        <!-- 实际图表 -->
        <ArtChart v-if="chartReady && currentItem" :option="chartOption" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
  import { ref, computed, nextTick } from 'vue'
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import { Loading } from '@element-plus/icons-vue'
  import type { WaterQualityData } from '@/types/water-quality'
  import waterQualityMockData from '@/mock/water-quality-data.json'
  import { WATER_QUALITY_THRESHOLDS } from '@/config/thresholds'
  import ArtChart from '@/components/core/charts/art-chart/index.vue'
  import type { EChartsOption } from '@/plugins/echarts'

  const props = defineProps<{
    data: WaterQualityData | null
  }>()

  interface MetricItem {
    key: string
    label: string
    value: number
    unit: string
    icon: string
    color: string
    status: 'normal' | 'warning' | 'danger'
  }

  // 指标颜色配置（硬编码 hex，ECharts canvas 无法解析 CSS 变量）
  const metricColors: Record<string, string> = {
    temperature: '#409EFF',
    ph: '#E6A23C',
    dissolvedOxygen: '#67C23A',
    ammoniaNitrogen: '#F56C6C',
    nitrite: '#9B59B6'
  }

  const items = computed<MetricItem[]>(() => {
    if (!props.data) return []

    const getStatus = (val: number, key: string) => {
      const rule = WATER_QUALITY_THRESHOLDS[key]
      if (!rule) return 'normal'
      if (rule.max !== undefined && val > rule.max) return 'warning'
      if (rule.min !== undefined && val < rule.min) return 'warning'
      return 'normal'
    }

    return [
      {
        key: 'temperature',
        label: '水温',
        value: props.data.temperature,
        unit: '℃',
        icon: 'ri:temp-hot-line',
        color: metricColors.temperature,
        status: getStatus(props.data.temperature, 'temperature')
      },
      {
        key: 'ph',
        label: 'pH值',
        value: props.data.ph,
        unit: '',
        icon: 'ri:test-tube-line',
        color: metricColors.ph,
        status: getStatus(props.data.ph, 'ph')
      },
      {
        key: 'dissolvedOxygen',
        label: '溶解氧',
        value: props.data.dissolvedOxygen,
        unit: 'mg/L',
        icon: 'ri:windy-line',
        color: metricColors.dissolvedOxygen,
        status: getStatus(props.data.dissolvedOxygen, 'dissolvedOxygen')
      },
      {
        key: 'ammoniaNitrogen',
        label: '氨氮',
        value: props.data.ammoniaNitrogen,
        unit: 'mg/L',
        icon: 'ri:flask-line',
        color: metricColors.ammoniaNitrogen,
        status: getStatus(props.data.ammoniaNitrogen, 'ammoniaNitrogen')
      },
      {
        key: 'nitrite',
        label: '亚硝酸盐',
        value: props.data.nitrite,
        unit: 'mg/L',
        icon: 'ri:drop-line',
        color: metricColors.nitrite,
        status: getStatus(props.data.nitrite, 'nitrite')
      }
    ]
  })

  const iconBoxStyle = (color: string) => ({
    color,
    backgroundColor: `color-mix(in oklch, ${color} 16%, transparent)`
  })

  const dialogVisible = ref(false)
  const currentItem = ref<MetricItem | null>(null)
  const chartReady = ref(false)

  const getStatusType = (status: string): 'success' | 'warning' | 'danger' | 'info' => {
    const map: Record<string, 'success' | 'warning' | 'danger' | 'info'> = {
      normal: 'success',
      warning: 'warning',
      danger: 'danger'
    }
    return map[status] || 'info'
  }

  const getStatusText = (status: string) => {
    const map: Record<string, string> = { normal: '正常', warning: '预警', danger: '告警' }
    return map[status] || '未知'
  }

  const handleCardClick = (item: MetricItem) => {
    currentItem.value = item
    dialogVisible.value = true
  }

  // 关键：dialog 动画结束后，延迟挂载图表
  const handleDialogOpened = async () => {
    await nextTick() // 等待 Vue 完成 DOM 更新
    chartReady.value = true // 此时才挂载 ArtChart
  }

  // dialog 关闭时重置状态
  const handleDialogClosed = () => {
    chartReady.value = false
  }

  // 图表配置，完全对齐 water-quality/index.vue
  const chartOption = computed<EChartsOption>(() => {
    if (!currentItem.value) return {}

    const config = currentItem.value
    const color = metricColors[config.key]

    const historyData = (waterQualityMockData as unknown as WaterQualityData[])
      .slice(0, 24)
      .reverse()

    const dates = historyData.map((d) => d.collectTime.split(' ')[1] || d.collectTime)
    const key = config.key as keyof WaterQualityData
    const values = historyData.map((d) => d[key] as number)

    return {
      tooltip: {
        trigger: 'axis',
        formatter: '{b} <br/> {a}: {c}' + config.unit,
        backgroundColor: 'rgba(50, 50, 50, 0.7)',
        borderColor: '#333',
        textStyle: { color: '#fff' }
      },
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
          end: 100
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
        axisLine: { lineStyle: { color: '#909399' } },
        axisLabel: { color: '#909399' }
      },
      yAxis: {
        type: 'value',
        axisLine: { lineStyle: { color: '#909399' } },
        axisLabel: { color: '#909399' },
        splitLine: {
          lineStyle: {
            color: '#E4E7ED',
            type: 'dashed',
            opacity: 0.3
          }
        }
      },
      series: [
        {
          name: config.label,
          type: 'line',
          smooth: true,
          showSymbol: false,
          data: values,
          itemStyle: { color },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color },
                { offset: 1, color: 'rgba(255, 255, 255, 0)' }
              ]
            },
            opacity: 0.3
          }
        }
      ]
    }
  })
</script>

<style scoped lang="scss">
  .water-quality-panel {
    .metric-card {
      cursor: pointer;
      // 移除强制背景色覆盖，使用全局深色规则 var(--default-box-color)
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
        border-left-color: var(--metric-accent, var(--el-color-primary));
        box-shadow: 0 12px 28px rgb(15 23 42 / 14%);
        transform: translateY(-3px) scale(1.02);
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
        text-transform: uppercase;
        letter-spacing: 0.04em;
      }

      .metric-main {
        align-items: baseline;
        margin-top: 14px;
        gap: 3px;
        line-height: 1;
      }

      .value {
        font-size: 28px;
        font-weight: 700;
        line-height: 1;
        color: var(--el-text-color-primary);
        font-variant-numeric: tabular-nums;
        letter-spacing: -0.02em;
      }

      .unit {
        font-size: 12px;
        line-height: 1;
        color: var(--el-text-color-secondary);
        font-weight: 500;
        letter-spacing: 0.02em;
        text-transform: uppercase;
      }

      :deep(.el-tag.status-tag) {
        padding: 0 7px;
      }
    }
  }

  :global(.dark) .water-quality-panel .metric-card {
    border-color: rgba(99, 179, 237, 0.25);
    border-left: 4px solid var(--metric-accent, var(--el-color-primary));
    box-shadow:
      0 2px 8px rgb(0 0 0 / 30%),
      inset 0 1px 0 rgba(99, 179, 237, 0.06);
    --el-card-bg-color: #224466 !important;

    &:hover {
      border-left-color: var(--metric-accent, var(--el-color-primary));
      box-shadow:
        0 12px 28px rgb(0 0 0 / 40%),
        0 0 0 1px rgba(99, 179, 237, 0.25);
      --el-card-bg-color: #2a5577 !important;
    }

    .icon-box {
      color: color-mix(in oklch, var(--metric-accent) 72%, var(--el-text-color-primary));
      background-color: color-mix(in oklch, var(--metric-accent) 12%, transparent);
    }
  }
</style>
