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

    <el-row :gutter="20">
      <!-- 左侧区域 -->
      <el-col :xs="24" :sm="24" :md="10" :lg="9">
        <div class="panel-section mb-5">
          <div class="section-title flex-c gap-2">
            <ArtSvgIcon icon="ri:temp-hot-line" />
            <span>水质监测指标 (模拟)</span>
          </div>
          <WaterQualityPanel :data="currentWaterQuality" />
        </div>

        <div class="panel-section mb-5">
          <div class="section-title flex-c gap-2">
            <ArtSvgIcon icon="ri:cpu-line" />
            <span>传感器设备状态 (模拟)</span>
          </div>
          <el-row :gutter="10">
            <el-col v-for="device in sensorDevices" :key="device.id" :span="12">
              <SensorCard :device="device" />
            </el-col>
          </el-row>
        </div>

        <AlertList :alerts="allAlerts" class="mb-5" />
        <FeedingPanel />
      </el-col>

      <!-- 右侧区域 -->
      <el-col :xs="24" :sm="24" :md="14" :lg="15">
        <HealthOverview :score="healthData.score" :risks="healthData.risks" class="mb-5" />

        <el-row :gutter="20" class="mb-5">
          <el-col :span="14">
            <VideoPlayer src="http://devimages.apple.com/iphone/samples/bipbop/gear1/prog_index.m3u8" />
          </el-col>
          <el-col :span="10">
            <AIDetectionResult :detection="latestDetection" />
          </el-col>
        </el-row>

        <!-- 生产数据预留 -->
        <el-card shadow="never" class="production-card">
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
      </el-col>
    </el-row>
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
  import { getRecentAlerts } from '@/api/alert'
  import { getHealthOverview } from '@/api/fish-disease/detect'
  import type { SensorDevice } from '@/types/device'
  import type { Alert } from '@/types/alert'
  import type { DetectionResult } from '@/types/fish-disease'
  import type { WaterQualityData } from '@/types/water-quality'
  import waterQualityMockData from '@/mock/water-quality-data.json'
  import { WATER_QUALITY_THRESHOLDS } from '@/config/thresholds'

  const lastUpdateTime = ref(new Date().toLocaleTimeString())
  const currentPond = ref('P001')
  const sensorDevices = ref<SensorDevice[]>([])
  const deviceAlerts = ref<Alert[]>([]) // 原有的设备告警

  // 水质数据相关状态
  const currentIndex = ref(0)
  const currentWaterQuality = ref<WaterQualityData | null>(null)

  // 基于当前水质数据生成的告警
  const waterQualityAlerts = computed<Alert[]>(() => {
    if (!currentWaterQuality.value) return []

    const alerts: Alert[] = []
    const data = currentWaterQuality.value
    const time = data.collectTime.split(' ')[1] || '刚刚'

    // 遍历检查每个指标
    Object.entries(WATER_QUALITY_THRESHOLDS).forEach(([key, rule]) => {
      // @ts-expect-error WATER_QUALITY_THRESHOLDS 为动态 key
      const val = data[key]
      if (typeof val === 'number') {
        if (rule.max !== undefined && val > rule.max) {
          alerts.push({
            id: `wq-${key}-high-${Date.now()}`,
            title: `${rule.label}过高`,
            message: `当前${rule.label} ${val}，超过阈值 ${rule.max}`,
            createTime: time,
            level: 'warning',
            type: 'water_quality',
            status: 'pending'
          })
        } else if (rule.min !== undefined && val < rule.min) {
          alerts.push({
            id: `wq-${key}-low-${Date.now()}`,
            title: `${rule.label}过低`,
            message: `当前${rule.label} ${val}，低于阈值 ${rule.min}`,
            createTime: time,
            level: 'warning',
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
      // @ts-expect-error mock 数据为动态索引访问
      currentWaterQuality.value = waterQualityMockData[currentIndex.value]
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
      // @ts-expect-error mock 数据为动态索引访问
      currentWaterQuality.value = waterQualityMockData[0]
    }
    refreshData()
  })
</script>

<style scoped lang="scss">
  .fishery-dashboard {
    padding: 20px;
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

    .section-title {
      padding-left: 10px;
      margin-bottom: 12px;
      font-size: 16px;
      font-weight: 700;
      color: var(--el-text-color-primary);
      border-left: 4px solid var(--el-color-primary);
    }

    .production-card {
      border: 1px solid var(--art-border-color);
      border-radius: 12px;

      :deep(.el-card__header) {
        border-bottom: 1px solid var(--art-border-color);
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
  }
</style>
