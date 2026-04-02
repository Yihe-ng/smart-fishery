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
        <el-tag type="success" effect="plain" class="flex-c gap-1">
          <ArtSvgIcon icon="ri:shield-check-line" />系统运行中
        </el-tag>
      </div>
    </div>

    <div class="dashboard-grid">
      <section class="panel-section dashboard-panel area-water">
        <div class="section-title flex-c gap-2">
          <ArtSvgIcon icon="ri:temp-hot-line" />
          <span>水质监测指标</span>
        </div>
        <div class="panel-content">
          <WaterQualityPanel :metrics="dashboardFrame?.metrics ?? null" />
        </div>
      </section>

      <AlertList
        :alerts="visibleAlerts"
        class="area-alert dashboard-card-base dashboard-fill"
        @resolve="handleResolveAlert"
      />

      <WeatherCard class="area-health dashboard-card-base dashboard-fill" />

      <section class="panel-section dashboard-panel area-sensor">
        <div class="section-title flex-c gap-2">
          <ArtSvgIcon icon="ri:cpu-line" />
          <span>传感器设备状态</span>
        </div>
        <div class="panel-content sensor-scroll">
          <el-row :gutter="10">
            <el-col v-for="device in sensorDevices" :key="device.id" :span="12">
              <SensorCard :device="device" />
            </el-col>
          </el-row>
        </div>
      </section>

      <VideoPlayer class="area-video dashboard-card-base dashboard-fill" :sources="videoSources" />

      <AIDetectionResult
        :detection="latestDetection"
        class="area-detect dashboard-card-base dashboard-fill"
      />

      <FeedingPanel class="area-feed dashboard-card-base dashboard-fill" />

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
              <div class="kpi-label">存栏预计</div>
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
  import { computed, onMounted, ref } from 'vue'
  import { ElMessage } from 'element-plus'

  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import WaterQualityPanel from './components/WaterQualityPanel.vue'
  import SensorCard from './components/SensorCard.vue'
  import AlertList from './components/AlertList.vue'
  import FeedingPanel from './components/FeedingPanel.vue'
  import WeatherCard from './components/WeatherCard.vue'
  import VideoPlayer from './components/VideoPlayer.vue'
  import AIDetectionResult from './components/AIDetectionResult.vue'

  import { getDashboardFrame } from '@/api/water-quality'
  import type { Alert } from '@/types/alert'
  import type { DetectionResult } from '@/types/fish-disease'
  import type { SensorDevice } from '@/types/device'
  import type { DashboardFrameResponse } from '@/types/water-quality'

  // 本地视频源列表
  const videoSources = [
    '/video/VID_20260330_161745.mp4',
    '/video/VID_20260330_161836.mp4',
    '/video/VID_20260330_161930.mp4',
    '/video/VID_20260330_162428.mp4',
    '/video/VID_20260330_163542.mp4',
    '/video/VID_20260330_163804.mp4'
  ]

  const lastUpdateTime = ref('--:--:--')
  const currentFrameIndex = ref(0)
  const nextFrameIndex = ref(0)
  const dashboardFrame = ref<DashboardFrameResponse | null>(null)
  const sensorDevices = ref<SensorDevice[]>([])
  const dismissedAlertIds = ref<string[]>([])

  const latestDetection = ref<DetectionResult>({
    id: 'd1',
    imageUrl:
      'https://images.unsplash.com/photo-1524704654690-b56c05c78a00?q=80&w=500&auto=format&fit=crop',
    detectTime: new Date().toISOString(),
    confidence: 94,
    diseaseType: 'gill_rot',
    bbox: { x: 30, y: 40, width: 25, height: 20 }
  })

  const visibleAlerts = computed(() => {
    const sourceAlerts = dashboardFrame.value?.alerts ?? []
    return sourceAlerts.filter((alert) => !dismissedAlertIds.value.includes(alert.id))
  })

  const applyFrame = (frame: DashboardFrameResponse) => {
    dashboardFrame.value = frame
    currentFrameIndex.value = frame.index
    nextFrameIndex.value = frame.nextIndex
    lastUpdateTime.value = frame.collectTime ?? '--'
    sensorDevices.value = frame.devices
    dismissedAlertIds.value = []
  }

  const loadDashboardFrame = async (index: number) => {
    const frame = await getDashboardFrame(index)
    applyFrame(frame)
  }

  const refreshData = async () => {
    try {
      await loadDashboardFrame(nextFrameIndex.value)
    } catch (error) {
      console.error('Failed to refresh dashboard frame:', error)
      ElMessage.error('刷新失败，请稍后重试')
    }
  }

  const handleResolveAlert = async (alert: Alert) => {
    dismissedAlertIds.value = [...dismissedAlertIds.value, alert.id]
    ElMessage.success('告警已忽略')
  }

  onMounted(() => {
    loadDashboardFrame(0).catch((error) => {
      console.error('Failed to initialize dashboard:', error)
      ElMessage.error('监测大屏初始化失败')
    })
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
          margin-bottom: 10px;
          font-size: 13px;
          font-weight: 500;
          color: var(--art-gray-600);
          text-transform: uppercase;
          letter-spacing: 0.06em;
        }

        .kpi-value {
          font-size: 32px;
          font-weight: 800;
          line-height: 1.1;
          color: var(--el-text-color-primary);
          font-variant-numeric: tabular-nums;
          letter-spacing: -0.02em;

          .kpi-unit {
            margin-left: 3px;
            font-size: 11px;
            font-weight: 500;
            color: var(--art-gray-500);
            text-transform: uppercase;
            letter-spacing: 0.04em;
          }
        }

        .kpi-trend {
          margin-top: 6px;
          font-size: 12px;
          font-weight: 600;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 2px;

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
      border-color: rgba(99, 179, 237, 0.1);
      box-shadow: 0 2px 12px rgb(0 0 0 / 50%);

      &:hover {
        border-color: rgba(99, 179, 237, 0.2);
        box-shadow: 0 4px 20px rgb(14 165 233 / 12%);
      }
    }

    .production-card {
      :deep(.el-card__header) {
        border-bottom: 1px solid rgba(99, 179, 237, 0.1);
      }
    }

    .area-water.dashboard-panel {
      background: var(--art-deep-surface-bg);
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
      border-color: rgba(99, 179, 237, 0.1);
      box-shadow: 0 2px 12px rgb(0 0 0 / 50%);

      &:hover {
        border-color: rgba(99, 179, 237, 0.2);
        box-shadow: 0 4px 20px rgb(14 165 233 / 12%);
      }
    }
  }
</style>
