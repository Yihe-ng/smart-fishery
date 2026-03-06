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
        <el-card shadow="hover" class="metric-card" @click="handleCardClick(item)">
          <div class="flex-cb">
            <div class="flex-c gap-2">
              <div
                class="icon-box"
                :style="{ backgroundColor: item.color + '20', color: item.color }"
              >
                <ArtSvgIcon :icon="item.icon" />
              </div>
              <span class="label">{{ item.label }}</span>
            </div>
            <el-tag :type="getStatusType(item.status)" size="small" effect="dark">
              {{ getStatusText(item.status) }}
            </el-tag>
          </div>
          <div class="mt-3 flex-baseline gap-1">
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
      @opened="initChart"
    >
      <div class="h-80 w-full" v-if="dialogVisible && currentItem">
        <div ref="chartRef" class="w-full h-full"></div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
  import { ref, computed, watch, nextTick, onBeforeUnmount } from 'vue'
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import type { WaterQualityData } from '@/types/water-quality'
  import waterQualityMockData from '@/mock/water-quality-data.json'
  import { WATER_QUALITY_THRESHOLDS } from '@/config/thresholds'
  import * as echarts from 'echarts/core'
  import { CanvasRenderer } from 'echarts/renderers'
  import { LineChart } from 'echarts/charts'
  import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'

  // 注册 ECharts 组件
  echarts.use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, LegendComponent])

  const props = defineProps<{
    data: WaterQualityData | null
  }>()

  const chartRef = ref<HTMLElement | null>(null)
  let chartInstance: echarts.ECharts | null = null

  interface MetricItem {
    key: string
    label: string
    value: number
    unit: string
    icon: string
    color: string
    status: 'normal' | 'warning' | 'danger'
  }

  const items = computed<MetricItem[]>(() => {
    if (!props.data) return []

    // 状态判断逻辑
    const getStatus = (val: number, key: string) => {
      const rule = WATER_QUALITY_THRESHOLDS[key]
      if (!rule) return 'normal'

      if (rule.max !== undefined && val > rule.max) return 'warning'
      if (rule.min !== undefined && val < rule.min) return 'warning'
      return 'normal'
    }

    return [
      {
        key: 'temperature', // 对应 JSON 字段名
        label: '水温',
        value: props.data.temperature,
        unit: '℃',
        icon: 'ri:temp-hot-line',
        color: '#409EFF', // var(--art-info) hex approximation
        status: getStatus(props.data.temperature, 'temperature')
      },
      {
        key: 'ph',
        label: 'pH值',
        value: props.data.ph,
        unit: '',
        icon: 'ri:test-tube-line',
        color: '#E6A23C', // var(--art-secondary) hex approximation
        status: getStatus(props.data.ph, 'ph')
      },
      {
        key: 'dissolvedOxygen',
        label: '溶解氧',
        value: props.data.dissolvedOxygen,
        unit: 'mg/L',
        icon: 'ri:windy-line',
        color: '#67C23A', // var(--art-success) hex approximation
        status: getStatus(props.data.dissolvedOxygen, 'dissolvedOxygen')
      },
      {
        key: 'ammoniaNitrogen',
        label: '氨氮',
        value: props.data.ammoniaNitrogen,
        unit: 'mg/L',
        icon: 'ri:flask-line',
        color: '#E6A23C', // var(--art-warning) hex approximation
        status: getStatus(props.data.ammoniaNitrogen, 'ammoniaNitrogen')
      },
      {
        key: 'nitrite',
        label: '亚硝酸盐',
        value: props.data.nitrite,
        unit: 'mg/L',
        icon: 'ri:drop-line',
        color: '#F56C6C', // var(--art-danger) hex approximation
        status: getStatus(props.data.nitrite, 'nitrite')
      }
    ]
  })

  const dialogVisible = ref(false)
  const currentItem = ref<MetricItem | null>(null)

  const getStatusType = (status: string) => {
    const map: any = { normal: 'success', warning: 'warning', danger: 'danger' }
    return map[status] || 'info'
  }

  const getStatusText = (status: string) => {
    const map: any = { normal: '正常', warning: '预警', danger: '告警' }
    return map[status] || '未知'
  }

  const handleCardClick = (item: MetricItem) => {
    currentItem.value = item
    dialogVisible.value = true
  }

  // 图表配置计算属性
  const chartOption = computed(() => {
    if (!currentItem.value) return {}

    // 获取历史数据
    // 注意：这里简单取最近24条数据作为示例，实际应根据时间筛选
    const historyData = (waterQualityMockData as unknown as WaterQualityData[])
      .slice(0, 24)
      .reverse() // 假设数据是按时间倒序的，图表需要正序

    const dates = historyData.map((d) => d.collectTime.split(' ')[1] || d.collectTime)
    // @ts-expect-error 动态字段用于图表值映射
    const values = historyData.map((d) => d[currentItem.value!.key])

    return {
      tooltip: {
        trigger: 'axis',
        formatter: '{b} <br/> {a}: {c}' + currentItem.value.unit,
        backgroundColor: 'rgba(50, 50, 50, 0.7)',
        borderColor: '#333',
        textStyle: {
          color: '#fff'
        }
      },
      grid: {
        top: '10%',
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: dates,
        axisLine: {
          lineStyle: {
            color: '#909399'
          }
        },
        axisLabel: {
          color: '#909399'
        }
      },
      yAxis: {
        type: 'value',
        axisLine: {
          lineStyle: {
            color: '#909399'
          }
        },
        axisLabel: {
          color: '#909399'
        },
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
          name: currentItem.value.label,
          type: 'line',
          smooth: true,
          showSymbol: false,
          data: values,
          itemStyle: {
            color: currentItem.value.color
          },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: currentItem.value.color },
                { offset: 1, color: 'rgba(255, 255, 255, 0)' }
              ]
            },
            opacity: 0.3
          }
        }
      ]
    }
  })

  // 初始化图表
  const initChart = async () => {
    await nextTick()
    if (chartRef.value) {
      if (chartInstance) {
        chartInstance.dispose()
      }
      chartInstance = echarts.init(chartRef.value)
      chartInstance.setOption(chartOption.value)
    }
  }

  // 监听选项变化更新图表
  watch(chartOption, (newVal) => {
    if (chartInstance) {
      chartInstance.setOption(newVal)
    }
  })

  // 监听窗口大小变化
  const handleResize = () => {
    chartInstance?.resize()
  }

  window.addEventListener('resize', handleResize)

  onBeforeUnmount(() => {
    window.removeEventListener('resize', handleResize)
    chartInstance?.dispose()
  })
</script>

<style scoped lang="scss">
  .water-quality-panel {
    .metric-card {
      cursor: pointer;
      border: 1px solid var(--art-border-color);
      transition: all 0.3s;

      &:hover {
        border-color: var(--el-color-primary);
        transform: translateY(-2px);
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
        color: var(--el-text-color-regular);
      }

      .value {
        font-size: 24px;
        font-weight: 700;
        color: var(--el-text-color-primary);
      }

      .unit {
        font-size: 12px;
        color: var(--el-text-color-secondary);
      }
    }
  }
</style>
