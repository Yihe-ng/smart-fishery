<template>
  <div class="production-page page-container">
    <el-row :gutter="20" class="mb-5">
      <el-col v-for="kpi in kpis" :key="kpi.label" :xs="12" :sm="12" :md="6">
        <el-card shadow="hover" class="kpi-card">
          <div class="flex-cb">
            <div class="icon-box" :style="{ color: kpi.color, backgroundColor: kpi.color + '15' }">
              <ArtSvgIcon :icon="kpi.icon" />
            </div>
            <div class="text-right">
              <div class="text-xs text-[var(--el-text-color-regular)]">{{ kpi.label }}</div>
              <div class="text-xl font-bold text-[var(--el-text-color-primary)]"
                >{{ kpi.value }}{{ kpi.unit }}</div
              >
            </div>
          </div>
          <div class="mt-3 pt-3 border-t border-[var(--default-border)] flex-cb text-xs">
            <span class="text-[var(--el-text-color-secondary)]">环比昨日</span>
            <span :class="kpi.trend > 0 ? 'text-green-500' : 'text-red-500'">
              {{ kpi.trend > 0 ? '+' : '' }}{{ kpi.trend }}%
              <ArtSvgIcon
                :icon="kpi.trend > 0 ? 'ri:arrow-right-up-line' : 'ri:arrow-right-down-line'"
              />
            </span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :span="16">
        <el-card shadow="never" class="mb-5">
          <template #header>
            <span class="font-bold">生长趋势分析</span>
          </template>
          <div
            class="h-80 bg-[var(--default-box-color)] border border-[var(--default-border)] rounded"
          >
            <el-loading v-loading="loading" element-loading-text="加载中..." fullscreen>
              <div ref="growthChartRef" class="w-full h-full"></div>
            </el-loading>
          </div>
        </el-card>

        <el-card shadow="never">
          <template #header>
            <span class="font-bold">投喂转化率 (FCR) 记录</span>
          </template>
          <el-table :data="fcrData" border>
            <el-table-column prop="date" label="统计日期" width="150" />
            <el-table-column prop="fishWeight" label="平均体重 (g)" align="center" />
            <el-table-column prop="feedTotal" label="累计投喂 (kg)" align="center" />
            <el-table-column prop="fcr" label="当前FCR" align="center">
              <template #default="{ row }">
                <el-tag :type="row.fcr < 1.6 ? 'success' : 'warning'" size="small">{{
                  row.fcr
                }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card shadow="never" class="mb-5">
          <template #header>
            <span class="font-bold">规格分布预估</span>
          </template>
          <div
            class="h-64 bg-[var(--default-box-color)] border border-[var(--default-border)] rounded"
          >
            <el-loading v-loading="loading" element-loading-text="加载中..." fullscreen>
              <div ref="sizeChartRef" class="w-full h-full"></div>
            </el-loading>
          </div>
        </el-card>

        <el-card shadow="never">
          <template #header>
            <span class="font-bold">最近盘点记录</span>
          </template>
          <el-timeline>
            <el-timeline-item
              v-for="record in inventoryData"
              :key="record.timestamp"
              :timestamp="record.timestamp"
              :type="record.type === '常规盘点' ? 'primary' : 'info'"
            >
              <p class="text-sm font-bold text-g-900">{{ record.type }}</p>
              <p class="text-xs text-g-500">存栏: {{ record.stock.toLocaleString() }}尾, 均重: {{ record.average_weight }}g</p>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
  import { ref, onMounted, onUnmounted } from 'vue'
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import { ElMessage } from 'element-plus'
  import * as echarts from 'echarts'
  import { getGrowthTrend, getSizeDistribution, getFCRRecords, getInventoryRecords } from '@/api/growth-monitoring/trend'

  // 状态定义
  const loading = ref(false)
  const growthChartRef = ref<HTMLElement | null>(null)
  const sizeChartRef = ref<HTMLElement | null>(null)
  let growthChart: echarts.ECharts | null = null
  let sizeChart: echarts.ECharts | null = null

  // KPI 数据
  const kpis = ref([
    {
      label: '预估存栏',
      value: '12,500',
      unit: '尾',
      icon: 'ri:group-line',
      color: 'var(--art-info)',
      trend: -0.2
    },
    {
      label: '平均体重',
      value: '450',
      unit: 'g',
      icon: 'ri:scales-line',
      color: 'var(--art-success)',
      trend: 1.5
    },
    {
      label: '今日死亡',
      value: '2',
      unit: '尾',
      icon: 'ri:alarm-warning-line',
      color: 'var(--art-danger)',
      trend: -50
    },
    {
      label: '投喂总量',
      value: '1,600',
      unit: 'g',
      icon: 'ri:restaurant-line',
      color: 'var(--art-warning)',
      trend: 5.2
    }
  ])

  // FCR 数据
  const fcrData = ref([
    { date: '2024-03-20', fishWeight: 450, feedTotal: 125.5, fcr: 1.55 },
    { date: '2024-03-13', fishWeight: 435, feedTotal: 118.2, fcr: 1.58 },
    { date: '2024-03-06', fishWeight: 420, feedTotal: 112.4, fcr: 1.62 }
  ])

  // 盘点记录数据
  const inventoryData = ref([
    { timestamp: '2024-03-15', type: '常规盘点', stock: 12500, average_weight: 450 },
    { timestamp: '2024-02-15', type: '常规盘点', stock: 12550, average_weight: 380 }
  ])

  // 初始化生长趋势图表
  const initGrowthChart = (data: any[]) => {
    if (!growthChartRef.value) return
    
    growthChart = echarts.init(growthChartRef.value)
    
    const dates = data.map(item => item.date)
    const weights = data.map(item => item.weight)
    const feeds = data.map(item => item.feed)
    
    const option = {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
          label: {
            backgroundColor: '#6a7985'
          }
        }
      },
      legend: {
        data: ['平均体重', '投喂量']
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: [
        {
          type: 'category',
          boundaryGap: false,
          data: dates
        }
      ],
      yAxis: [
        {
          type: 'value',
          name: '平均体重 (g)',
          min: Math.min(...weights) * 0.9,
          max: Math.max(...weights) * 1.1
        },
        {
          type: 'value',
          name: '投喂量 (g)',
          min: Math.min(...feeds) * 0.9,
          max: Math.max(...feeds) * 1.1
        }
      ],
      series: [
        {
          name: '平均体重',
          type: 'line',
          data: weights,
          smooth: true,
          lineStyle: {
            width: 3,
            color: '#409EFF'
          },
          itemStyle: {
            color: '#409EFF'
          }
        },
        {
          name: '投喂量',
          type: 'line',
          yAxisIndex: 1,
          data: feeds,
          smooth: true,
          lineStyle: {
            width: 3,
            color: '#67C23A'
          },
          itemStyle: {
            color: '#67C23A'
          }
        }
      ]
    }
    
    growthChart.setOption(option)
  }

  // 初始化规格分布图表
  const initSizeChart = (data: any[]) => {
    if (!sizeChartRef.value) return
    
    sizeChart = echarts.init(sizeChartRef.value)
    
    const option = {
      tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b}: {c} ({d}%)'
      },
      legend: {
        orient: 'vertical',
        left: 'left',
        data: data.map(item => item.size_range)
      },
      series: [
        {
          name: '规格分布',
          type: 'pie',
          radius: '60%',
          data: data.map(item => ({
            value: item.percentage,
            name: item.size_range
          })),
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }
      ]
    }
    
    sizeChart.setOption(option)
  }

  // 加载数据
  const loadData = async () => {
    loading.value = true
    try {
      // 获取生长趋势数据
      const growthData = await getGrowthTrend()
      if (growthData) {
        initGrowthChart(growthData)
      }
      
      // 获取规格分布数据
      const sizeData = await getSizeDistribution()
      if (sizeData) {
        initSizeChart(sizeData)
      }
      
      // 获取 FCR 数据
      const fcrRecords = await getFCRRecords()
      if (fcrRecords) {
        fcrData.value = fcrRecords
      }
      
      // 获取盘点记录
      const inventoryRecords = await getInventoryRecords()
      if (inventoryRecords) {
        inventoryData.value = inventoryRecords
      }
    } catch (error) {
      console.error('加载数据失败:', error)
      ElMessage.error('加载数据失败，请重试')
    } finally {
      loading.value = false
    }
  }

  // 监听窗口大小变化
  const handleResize = () => {
    growthChart?.resize()
    sizeChart?.resize()
  }

  onMounted(() => {
    loadData()
    window.addEventListener('resize', handleResize)
  })

  onUnmounted(() => {
    growthChart?.dispose()
    sizeChart?.dispose()
    window.removeEventListener('resize', handleResize)
  })
</script>

<style scoped lang="scss">
  .production-page {
    padding: 20px;
    background-color: var(--default-bg-color);

    .kpi-card {
      border: 1px solid var(--default-border);

      .icon-box {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 44px;
        height: 44px;
        font-size: 22px;
        border-radius: 10px;
      }
    }
  }
</style>
