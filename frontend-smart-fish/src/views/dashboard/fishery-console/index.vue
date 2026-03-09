<template>
  <div class="fishery-dashboard page-container">
    <div class="dashboard-header flex-cb mb-5">
      <div class="flex-c gap-3">
        <div class="title-icon">
          <ArtSvgIcon icon="ri:anchor-line" />
        </div>
        <div>
          <h2 class="text-2xl font-bold text-[var(--el-text-color-primary)]">1号养殖池实时监控</h2>
          <p class="text-sm text-[var(--el-text-color-regular)]">
            最后更新: {{ lastUpdateTime }}
            <el-link type="primary" :underline="false" class="ml-2" @click="refreshData">
              <ArtSvgIcon icon="ri:refresh-line" class="mr-1" />刷新
            </el-link>
          </p>
        </div>
      </div>
      <div class="flex-c gap-4">
        <el-radio-group v-model="currentPond" size="small">
          <el-radio-button label="P001">
            <div class="flex-c gap-1"><ArtSvgIcon icon="ri:database-2-line" />1号试验池</div>
          </el-radio-button>
          <el-radio-button label="P002">
            <div class="flex-c gap-1"><ArtSvgIcon icon="ri:database-2-line" />2号试验池</div>
          </el-radio-button>
        </el-radio-group>
        <el-tag type="success" effect="plain" class="flex-c gap-1">
          <ArtSvgIcon icon="ri:shield-check-line" />系统运行中
        </el-tag>
      </div>
    </div>

    <div class="dashboard-grid">
      <section class="panel-section dashboard-panel area-water">
        <div class="section-title flex-c gap-2">
          <ArtSvgIcon icon="ri:temp-hot-line" />
          <span>水质监测指标 (模拟)</span>
        </div>
        <div class="panel-content">
          <WaterQualityPanel :data="currentWaterQuality" />
        </div>
      </section>

      <AlertList
        :alerts="allAlerts"
        class="area-alert dashboard-card-base dashboard-fill"
        @view="handleViewAlert"
        @resolve="handleResolveAlert"
      />

      <HealthOverview
        :score="healthData.score"
        :risks="healthData.risks"
        class="area-health dashboard-card-base dashboard-fill"
      />

      <section class="panel-section dashboard-panel area-sensor">
        <div class="section-title flex-c gap-2">
          <ArtSvgIcon icon="ri:cpu-line" />
          <span>传感器设备状态 (模拟)</span>
        </div>
        <div class="panel-content sensor-scroll">
          <el-row :gutter="10">
            <el-col v-for="device in sensorDevices" :key="device.id" :span="12">
              <SensorCard :device="device" />
            </el-col>
          </el-row>
        </div>
      </section>

      <VideoPlayer
        class="area-video dashboard-card-base dashboard-fill"
        src="http://devimages.apple.com/iphone/samples/bipbop/gear1/prog_index.m3u8"
      />

      <AIDetectionResult
        :detection="latestDetection"
        class="area-detect dashboard-card-base dashboard-fill"
      />

      <FeedingPanel class="area-feed dashboard-card-base dashboard-fill" />

      <!-- 生产数据预留 -->
      <el-card shadow="never" class="production-card area-kpi dashboard-card-base dashboard-fill">
        <template #header>
          <div class="flex-cb">
            <div class="flex-c gap-2">
              <ArtSvgIcon icon="ri:bar-chart-box-line" class="text-blue-500" />
              <span class="font-bold">生产关键指标 (KPI) (模拟)</span>
            </div>
            <el-button link type="primary" icon="ri:file-list-3-line">查看报表</el-button>
          </div>
        </template>
        <el-row :gutter="20">
          <el-col :span="8">
            <div class="kpi-item">
              <div class="kpi-label">当前估重 (Avg)</div>
              <div class="kpi-value">450<span class="kpi-unit">g</span></div>
              <div class="kpi-trend up"><ArtSvgIcon icon="ri:arrow-right-up-line" /> 5.2%</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="kpi-item">
              <div class="kpi-label">存栏预估</div>
              <div class="kpi-value">12,500<span class="kpi-unit">尾</span></div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="kpi-item">
              <div class="kpi-label">投喂量 (今日)</div>
              <div class="kpi-value">1,600<span class="kpi-unit">g</span></div>
            </div>
          </el-col>
        </el-row>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { ref, onMounted, computed } from 'vue'
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import WaterQualityPanel from './components/WaterQualityPanel.vue'
  import SensorCard from './components/SensorCard.vue'
  import AlertList from './components/AlertList.vue'
  import FeedingPanel from './components/FeedingPanel.vue'
  import HealthOverview from './components/HealthOverview.vue'
  import VideoPlayer from './components/VideoPlayer.vue'
  import AIDetectionResult from './components/AIDetectionResult.vue'

  import { getSensorDevices } from '@/api/device'
  import { getRecentAlerts, resolveAlert } from '@/api/alert'
  import { getHealthOverview } from '@/api/fish-disease/detect'
  import type { SensorDevice } from '@/types/device'
  import type { Alert } from '@/types/alert'
  import type { DetectionResult } from '@/types/fish-disease'
  import type { WaterQualityData } from '@/types/water-quality'
  import waterQualityMockData from '@/mock/water-quality-data.json'
  import { WATER_QUALITY_THRESHOLDS } from '@/config/thresholds'
  import { ElMessage } from 'element-plus'

  interface WaterQualityMockRow {
    collectTime: string
    temperature: number
    ph: number
    dissolvedOxygen: number
    ammoniaNitrogen: number
    nitrite: number
    status: string
  }

  const lastUpdateTime = ref(new Date().toLocaleTimeString())
  const currentPond = ref('P001')
  const sensorDevices = ref<SensorDevice[]>([])
  const deviceAlerts = ref<Alert[]>([]) // 原有的设备告警

  // 水质数据相关状态
  const currentIndex = ref(0)
  const currentWaterQuality = ref<WaterQualityData | null>(null)

  const parseMockWaterQuality = (row: WaterQualityMockRow, index: number): WaterQualityData => {
    const normalizedStatus: WaterQualityData['status'] =
      row.status === 'danger' || row.status === 'warning' ? row.status : 'normal'

    return {
      id: `mock-${index}`,
      collectTime: row.collectTime,
      temperature: row.temperature,
      ph: row.ph,
      dissolvedOxygen: row.dissolvedOxygen,
      ammoniaNitrogen: row.ammoniaNitrogen,
      nitrite: row.nitrite,
      status: normalizedStatus
    }
  }

  type WaterMetricKey = keyof Pick<
    WaterQualityData,
    'temperature' | 'ph' | 'dissolvedOxygen' | 'ammoniaNitrogen' | 'nitrite'
  >

  // 基于当前水质数据生成的告警
  const waterQualityAlerts = computed<Alert[]>(() => {
    if (!currentWaterQuality.value) return []

    const alerts: Alert[] = []
    const data = currentWaterQuality.value
    const time = data.collectTime.split(' ')[1] || '刚刚'

    // 遍历检查每个指标
    Object.entries(WATER_QUALITY_THRESHOLDS).forEach(([rawKey, rule]) => {
      const key = rawKey as WaterMetricKey
      const val = data[key]
      if (typeof val === 'number') {
        const isDangerHigh = rule.max !== undefined && val > rule.max * 1.2
        const isDangerLow = rule.min !== undefined && val < rule.min * 0.8
        const level: Alert['level'] = isDangerHigh || isDangerLow ? 'critical' : 'warning'

        if (rule.max !== undefined && val > rule.max) {
          alerts.push({
            id: `wq-${key}-high-${Date.now()}`,
            title: `${rule.label}过高`,
            message: `当前${rule.label} ${val}，超过阈值 ${rule.max}`,
            createTime: time,
            level,
            type: 'water_quality',
            status: 'pending'
          })
        } else if (rule.min !== undefined && val < rule.min) {
          alerts.push({
            id: `wq-${key}-low-${Date.now()}`,
            title: `${rule.label}过低`,
            message: `当前${rule.label} ${val}，低于阈值 ${rule.min}`,
            createTime: time,
            level,
            type: 'water_quality',
            status: 'pending'
          })
        }
      }
    })

    return alerts
  })

  // 混合显示所有告警，优先显示水质告警
  const allAlerts = computed(() => {
    return [...waterQualityAlerts.value, ...deviceAlerts.value]
  })

  const handleViewAlert = (alert: Alert) => {
    ElMessage.info(`查看告警：${alert.title}`)
  }

  const handleResolveAlert = async (alert: Alert) => {
    try {
      await resolveAlert(alert.id)
      deviceAlerts.value = deviceAlerts.value.filter((item) => item.id !== alert.id)
      ElMessage.success('告警已忽略')
    } catch (error) {
      console.error('resolve alert failed:', error)
      ElMessage.error('告警处理失败，请稍后重试')
    }
  }

  const healthData = ref<{
    score: number
    risks: {
      gillRot: 'low' | 'medium' | 'high'
      redSkin: 'low' | 'medium' | 'high'
      enteritis: 'low' | 'medium' | 'high'
    }
  }>({
    score: 0,
    risks: { gillRot: 'low', redSkin: 'low', enteritis: 'low' }
  })

  const latestDetection = ref<DetectionResult>({
    id: 'd1',
    imageUrl:
      'https://images.unsplash.com/photo-1524704654690-b56c05c78a00?q=80&w=500&auto=format&fit=crop',
    detectTime: new Date().toISOString(),
    confidence: 94,
    diseaseType: 'gill_rot',
    bbox: { x: 30, y: 40, width: 25, height: 20 }
  })

  const refreshData = async () => {
    lastUpdateTime.value = new Date().toLocaleTimeString()

    // 更新水质数据（循环切换下一条）
    if (waterQualityMockData && waterQualityMockData.length > 0) {
      currentIndex.value = (currentIndex.value + 1) % waterQualityMockData.length
      const current = waterQualityMockData[currentIndex.value] as WaterQualityMockRow
      currentWaterQuality.value = parseMockWaterQuality(current, currentIndex.value)
    }

    try {
      const [devices, recentAlerts, health] = await Promise.all([
        getSensorDevices(),
        getRecentAlerts(),
        getHealthOverview()
      ])
      sensorDevices.value = devices
      deviceAlerts.value = recentAlerts
      healthData.value = health
    } catch (err) {
      console.error('Failed to refresh dashboard data:', err)
    }

    // TODO: 接入 WebSocket 实时告警推送
    // 示例：
    // socket.on('alert', (newAlert) => {
    //   deviceAlerts.value.unshift(newAlert)
    // })
  }

  onMounted(() => {
    // 初始化第一条数据
    if (waterQualityMockData && waterQualityMockData.length > 0) {
      const first = waterQualityMockData[0] as WaterQualityMockRow
      currentWaterQuality.value = parseMockWaterQuality(first, 0)
    }
    refreshData()
  })
</script>

<style scoped lang="scss">
  .fishery-dashboard {
    padding: 20px;
    background-color: var(--art-bg-color);
    background-color: var(--art-bg-color);

    .dashboard-header {
      .title-icon {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 48px;
        height: 48px;
        font-size: 24px;
        color: white;
        background: linear-gradient(135deg, var(--el-color-primary) 0%, #38c0fc 100%);
        border-radius: 12px;
        box-shadow: 0 4px 12px rgb(14 165 233 / 30%);
      }
    }

    .dashboard-grid {
      display: grid;
      grid-template-columns: 1.1fr 1.25fr 1fr;
      grid-template-rows: 340px 360px auto;
      gap: 20px;
      grid-template-areas:
        'water alert health'
        'sensor video detect'
        'feed kpi kpi';
      align-items: stretch;
    }

    .area-water {
      grid-area: water;
    }

    .area-alert {
      grid-area: alert;
    }

    .area-health {
      grid-area: health;
    }

    .area-sensor {
      grid-area: sensor;
    }

    .area-video {
      grid-area: video;
    }

    .area-detect {
      grid-area: detect;
    }

    .area-feed {
      grid-area: feed;
    }

    .area-kpi {
      grid-area: kpi;
    }

    .dashboard-fill {
      height: 100%;
      min-height: 0;
    }

    .dashboard-panel {
      display: flex;
      flex-direction: column;
      min-height: 0;
      padding: 12px 12px 0;
      background: var(--default-box-color);
      border: 1px solid var(--art-card-border);
      border-radius: 12px;
      box-shadow: 0 2px 8px rgb(0 0 0 / 6%);
      transition: box-shadow 0.2s ease;

      &:hover {
        box-shadow: 0 4px 16px rgb(0 0 0 / 10%);
      }
    }

    .panel-content {
      flex: 1;
      min-height: 0;
    }

    .sensor-scroll {
      overflow: auto;
      padding-right: 4px;
    }

    .section-title {
      padding-left: 10px;
      margin-bottom: 12px;
      font-size: 16px;
      font-weight: 700;
      color: var(--el-text-color-primary);
      border-left: 4px solid var(--el-color-primary);
    }

    .production-card {
      :deep(.el-card__header) {
        border-bottom: 1px solid var(--art-card-border);
      }

      :deep(.el-card__body) {
        height: calc(100% - 57px);
      }

      .kpi-item {
        padding: 10px 0;
        text-align: center;

        .kpi-label {
          margin-bottom: 8px;
          font-size: 14px;
          color: var(--el-text-color-regular);
        }

        .kpi-value {
          font-size: 24px;
          font-weight: 800;
          color: var(--el-text-color-primary);

          .kpi-unit {
            margin-left: 2px;
            font-size: 12px;
            font-weight: normal;
          }
        }

        .kpi-trend {
          margin-top: 4px;
          font-size: 12px;

          &.up {
            color: var(--el-color-success);
          }

          &.down {
            color: var(--el-color-danger);
          }
        }
      }
    }

    @media (width <= 1200px) {
      .dashboard-grid {
        grid-template-columns: 1fr 1fr;
        grid-template-rows: auto;
        grid-template-areas:
          'water alert'
          'health health'
          'sensor video'
          'detect feed'
          'kpi kpi';
      }
    }

    @media (width <= 768px) {
      .dashboard-grid {
        grid-template-columns: 1fr;
        grid-template-areas:
          'video'
          'alert'
          'health'
          'water'
          'detect'
          'sensor'
          'feed'
          'kpi';
      }
    }
  }

  :global(.dark) .fishery-dashboard {
    .dashboard-panel {
      border-color: rgba(255 255 255 / 0.06);
      box-shadow: 0 2px 8px rgb(0 0 0 / 40%);

      &:hover {
        box-shadow: 0 4px 16px rgb(0 0 0 / 50%);
      }
    }

    .production-card {
      :deep(.el-card__header) {
        border-bottom: 1px solid rgba(255 255 255 / 0.06);
      }
    }
  }
</style>

<style lang="scss">
  .fishery-dashboard {
    .dashboard-card-base {
      background: var(--default-box-color);
      border: 1px solid var(--art-card-border);
      border-radius: 12px;
      box-shadow: 0 2px 8px rgb(0 0 0 / 6%);
      transition: box-shadow 0.2s ease;

      &:hover {
        box-shadow: 0 4px 16px rgb(0 0 0 / 10%);
      }
    }
  }

  :global(.dark) .fishery-dashboard {
    .dashboard-card-base {
      border-color: rgba(255 255 255 / 0.06);
      box-shadow: 0 2px 8px rgb(0 0 0 / 40%);

      &:hover {
        box-shadow: 0 4px 16px rgb(0 0 0 / 50%);
      }
    }
  }
</style>
