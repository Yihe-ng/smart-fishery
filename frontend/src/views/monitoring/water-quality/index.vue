<template>
  <div class="water-quality-page page-container">
    <el-card shadow="never" class="mb-5">
      <template #header>
        <div class="flex-cb">
          <div class="flex-c gap-2">
            <ArtSvgIcon icon="ri:line-chart-line" class="text-blue-500" />
            <span class="font-bold">24小时趋势分析</span>
          </div>
          <el-radio-group v-model="selectedMetric" size="small">
            <el-radio-button label="temperature">
              <div class="flex-c gap-1"><ArtSvgIcon icon="ri:temp-hot-line" />水温</div>
            </el-radio-button>
            <el-radio-button label="ph">
              <div class="flex-c gap-1"><ArtSvgIcon icon="ri:test-tube-line" />pH值</div>
            </el-radio-button>
            <el-radio-button label="dissolvedOxygen">
              <div class="flex-c gap-1"><ArtSvgIcon icon="ri:windy-line" />溶解氧</div>
            </el-radio-button>
            <el-radio-button label="ammoniaNitrogen">
              <div class="flex-c gap-1"><ArtSvgIcon icon="ri:flask-line" />氨氮</div>
            </el-radio-button>
            <el-radio-button label="nitrite">
              <div class="flex-c gap-1"><ArtSvgIcon icon="ri:drop-line" />亚硝酸盐</div>
            </el-radio-button>
          </el-radio-group>
        </div>
      </template>
      <div
        class="chart-container h-80 w-full bg-[var(--default-box-color)] border border-[var(--default-border)] rounded p-4"
      >
        <ArtChart :option="chartOption" />
      </div>
    </el-card>

    <el-card shadow="never">
      <template #header>
        <div class="flex-cb">
          <span class="font-bold">历史监测记录</span>
          <div class="flex-c gap-2">
            <el-button size="small" @click="handleExport">
              <template #icon><ArtSvgIcon icon="ri:download-2-line" /></template>
              导出数据
            </el-button>
          </div>
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
  import { ref, onMounted, reactive, computed } from 'vue'
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import ArtSearchBar from '@/components/core/forms/art-search-bar/index.vue'
  import type { WaterQualityData } from '@/types/water-quality'
  import type { SearchFormItem } from '@/components/core/forms/art-search-bar/index.vue'
  import waterQualityMockData from '@/mock/water-quality-data.json'
  import ArtChart from '@/components/core/charts/art-chart/index.vue'
  import type { EChartsOption } from '@/plugins/echarts'
  import { WATER_QUALITY_THRESHOLDS } from '@/config/thresholds'

  const selectedMetric = ref('temperature')

  // 指标配置
  const metricConfig: Record<string, { label: string; unit: string; color: string }> = {
    temperature: { label: '水温', unit: '℃', color: '#409EFF' },
    ph: { label: 'pH值', unit: '', color: '#E6A23C' },
    dissolvedOxygen: { label: '溶解氧', unit: 'mg/L', color: '#67C23A' },
    ammoniaNitrogen: { label: '氨氮', unit: 'mg/L', color: '#E6A23C' },
    nitrite: { label: '亚硝酸盐', unit: 'mg/L', color: '#F56C6C' }
  }

  const chartOption = computed<EChartsOption>(() => {
    const config = metricConfig[selectedMetric.value]

    // 使用 loadData 中获取的响应式数据
    const dataToDisplay = chartDataList.value

    const dates = dataToDisplay.map((item) => item.collectTime.split(' ')[1] || item.collectTime)
    // @ts-expect-error 指标 key 为动态选择
    const values = dataToDisplay.map((item) => item[selectedMetric.value])

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
          itemStyle: { color: config.color },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: config.color },
                { offset: 1, color: 'rgba(255, 255, 255, 0)' }
              ]
            },
            opacity: 0.3
          }
        }
      ]
    }
  })

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
  const currentPage = ref(1)
  const pageSize = ref(10)
  const total = ref(0)
  // 图表数据
  const chartDataList = ref<WaterQualityData[]>([])

  const loadData = async () => {
    try {
      // TODO: 替换为真实后端分页接口
      // 模拟后端分页逻辑
      let filteredData = waterQualityMockData as unknown as WaterQualityData[]

      // 日期筛选
      if (searchQuery.dateRange && searchQuery.dateRange.length === 2) {
        const [start, end] = searchQuery.dateRange
        filteredData = filteredData.filter((item) => {
          const itemDate = item.collectTime.split(' ')[0]
          return itemDate >= start && itemDate <= end
        })
      }

      // 逻辑判断：是否超出阈值
      const checkStatus = (item: WaterQualityData): WaterQualityData['status'] => {
        for (const key in WATER_QUALITY_THRESHOLDS) {
          const rule = WATER_QUALITY_THRESHOLDS[key]
          // @ts-expect-error 阈值对象使用动态 key 访问
          const val = item[key]
          if (rule.max !== undefined && val > rule.max) return 'warning'
          if (rule.min !== undefined && val < rule.min) return 'warning'
        }
        return 'normal'
      }

      // 更新所有数据的状态（前端计算）
      const processedData: WaterQualityData[] = filteredData.map((item) => ({
        ...item,
        status: checkStatus(item)
      }))

      total.value = processedData.length

      // 图表使用所有符合筛选条件的数据
      chartDataList.value = processedData.slice(0, 50).reverse()

      // 分页切片
      const start = (currentPage.value - 1) * pageSize.value
      const end = start + pageSize.value
      tableData.value = processedData.slice(start, end)
    } catch (err) {
      console.error('Failed to load water quality history:', err)
    }
  }

  const handleSearchQueryUpdate = (value: { dateRange: string[] }) => {
    searchQuery.dateRange = value?.dateRange || []
  }

  const handleReset = () => {
    searchQuery.dateRange = []
    currentPage.value = 1 // 重置页码
    loadData()
  }

  const handleExport = () => {
    console.log('Exporting data...')
  }

  // 监听分页变化
  const handleSizeChange = (val: number) => {
    pageSize.value = val
    loadData()
  }

  const handleCurrentChange = (val: number) => {
    currentPage.value = val
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
