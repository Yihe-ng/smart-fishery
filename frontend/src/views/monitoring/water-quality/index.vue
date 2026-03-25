<template>
  <div class="page-container water-quality-page">
    <el-card shadow="never" class="mb-5">
      <template #header>
        <div class="flex-cb">
          <div class="flex-c gap-2">
            <ArtSvgIcon icon="ri:line-chart-line" class="text-theme" />
            <span class="font-bold">24 小时趋势分析</span>
          </div>

          <el-radio-group v-model="selectedMetric" size="small">
            <el-radio-button v-for="metric in metricOptions" :key="metric.key" :label="metric.key">
              <div class="flex-c gap-1">
                <ArtSvgIcon :icon="metric.icon" />
                {{ metric.label }}
              </div>
            </el-radio-button>
          </el-radio-group>
        </div>
      </template>

      <div
        class="chart-container h-80 w-full rounded border border-[var(--default-border)] bg-[var(--default-box-color)] p-4"
      >
        <ArtChart :option="chartOption" />
      </div>
    </el-card>

    <el-card shadow="never">
      <template #header>
        <div class="flex-cb">
          <span class="font-bold">历史监测记录</span>
          <el-button size="small" @click="handleExport">
            <template #icon>
              <ArtSvgIcon icon="ri:download-2-line" />
            </template>
            导出数据
          </el-button>
        </div>
      </template>

      <div class="mb-4">
        <ArtSearchBar
          :model-value="searchQuery"
          :items="searchItems"
          :show-expand="false"
          @update:model-value="handleSearchQueryUpdate"
          @search="loadData"
          @reset="handleReset"
        />
      </div>

      <el-table :data="tableData" border style="width: 100%">
        <el-table-column prop="collectTime" label="采集时间" width="180" />
        <el-table-column prop="temperature" label="水温 (℃)" align="center" />
        <el-table-column prop="ph" label="pH值" align="center" />
        <el-table-column prop="dissolvedOxygen" label="溶解氧 (mg/L)" align="center" />
        <el-table-column prop="ammoniaNitrogen" label="氨氮 (mg/L)" align="center" />
        <el-table-column prop="nitrite" label="亚硝酸盐 (mg/L)" align="center" />
        <el-table-column prop="status" label="状态" align="center" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'normal' ? 'success' : 'warning'" size="small">
              {{ row.status === 'normal' ? '正常' : '异常' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>

      <div class="mt-4 flex justify-end">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
  import { computed, onMounted, reactive, ref } from 'vue'
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import ArtSearchBar from '@/components/core/forms/art-search-bar/index.vue'
  import ArtChart from '@/components/core/charts/art-chart/index.vue'
  import { WATER_QUALITY_THRESHOLDS } from '@/config/thresholds'
  import {
    WATER_QUALITY_METRIC_ORDER,
    WATER_QUALITY_METRICS,
    getWaterQualityMetricColor
  } from '@/config/theme'
  import { useChartStyles } from '@/hooks/core/useChart'
  import { getWaterQualityHistory } from '@/api/water-quality'
  import type { SearchFormItem } from '@/components/core/forms/art-search-bar/index.vue'
  import type { EChartsOption } from '@/plugins/echarts'
  import type { WaterQualityData } from '@/types/water-quality'

  const { getAxisLineStyle, getAxisLabelStyle, getSplitLineStyle, getTooltipStyle } =
    useChartStyles()

  const metricOptions = WATER_QUALITY_METRIC_ORDER.map((key) => WATER_QUALITY_METRICS[key])
  const selectedMetric = ref<(typeof WATER_QUALITY_METRIC_ORDER)[number]>('temperature')

  const searchQuery = reactive({
    dateRange: [] as string[]
  })

  const searchItems: SearchFormItem[] = [
    {
      label: '统计周期',
      key: 'dateRange',
      type: 'daterange',
      props: {
        rangeSeparator: '至',
        startPlaceholder: '开始日期',
        endPlaceholder: '结束日期',
        valueFormat: 'YYYY-MM-DD'
      },
      span: 12
    }
  ]

  const tableData = ref<WaterQualityData[]>([])
  const chartDataList = ref<WaterQualityData[]>([])
  const currentPage = ref(1)
  const pageSize = ref(10)
  const total = ref(0)

  const chartOption = computed<EChartsOption>(() => {
    const metric = WATER_QUALITY_METRICS[selectedMetric.value]
    const color = getWaterQualityMetricColor(selectedMetric.value)
    const dates = chartDataList.value.map(
      (item) => item.collectTime.split(' ')[1] || item.collectTime
    )
    const values = chartDataList.value.map((item) => item[selectedMetric.value] as number)

    return {
      tooltip: getTooltipStyle('axis', {
        triggerOn: 'mousemove|click',
        axisPointer: {
          type: 'line',
          snap: true,
          animation: false
        },
        formatter: `{b}<br />${metric.label}: {c}${metric.unit}`
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
          name: metric.label,
          type: 'line',
          smooth: true,
          showSymbol: false,
          emphasis: {
            focus: 'none'
          },
          data: values,
          itemStyle: { color },
          lineStyle: { color },
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
            opacity: 0.28
          }
        }
      ]
    }
  })

  const loadData = async () => {
    const startTime = searchQuery.dateRange.length === 2 ? searchQuery.dateRange[0] + ' 00:00:00' : undefined
    const endTime = searchQuery.dateRange.length === 2 ? searchQuery.dateRange[1] + ' 23:59:59' : undefined

    const res = await getWaterQualityHistory({
      pageNum: currentPage.value,
      pageSize: pageSize.value,
      startTime,
      endTime
    })

    total.value = res.total
    tableData.value = res.list

    const chartRes = await getWaterQualityHistory({
      pageNum: 1,
      pageSize: 100,
      startTime,
      endTime
    })
    chartDataList.value = chartRes.list
      .slice()
      .sort((a: WaterQualityData, b: WaterQualityData) => a.collectTime.localeCompare(b.collectTime))
  }

  const getRowStatus = (item: WaterQualityData): WaterQualityData['status'] => {
    for (const key of WATER_QUALITY_METRIC_ORDER) {
      const rule = WATER_QUALITY_THRESHOLDS[key]
      const value = item[key] as number

      if (
        (rule.max !== undefined && value > rule.max) ||
        (rule.min !== undefined && value < rule.min)
      ) {
        return 'warning'
      }
    }

    return 'normal'
  }

  const handleSearchQueryUpdate = (value: { dateRange: string[] }) => {
    searchQuery.dateRange = value?.dateRange || []
  }

  const handleReset = () => {
    searchQuery.dateRange = []
    currentPage.value = 1
    loadData()
  }

  const handleExport = () => {
    console.log('Export water quality data')
  }

  const handleSizeChange = (value: number) => {
    pageSize.value = value
    loadData()
  }

  const handleCurrentChange = (value: number) => {
    currentPage.value = value
    loadData()
  }

  onMounted(() => {
    loadData()
  })
</script>

<style scoped lang="scss">
  .water-quality-page {
    padding: 20px;
  }
</style>
