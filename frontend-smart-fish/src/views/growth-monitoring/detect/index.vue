<template>
  <div class="growth-monitoring-detect">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="title-section">
        <ArtSvgIcon icon="ri:scales-3-line" style="font-size: 32px; color: #409eff" />
        <h2>智能鱼类生长识别系统</h2>
      </div>
      <el-tag :type="isCameraActive ? 'success' : 'info'" size="large" effect="dark">
        <ArtSvgIcon v-if="isCameraActive" icon="ri:loader-4-line" class="animate-spin mr-1" />
        {{ isCameraActive ? '系统监控中' : '系统待命' }}
      </el-tag>
    </div>

    <el-row :gutter="20">
      <!-- 左侧控制面板 -->
      <el-col :xs="24" :sm="24" :md="8" :lg="6">
        <GrowthControlPanel v-model="confidence" class="mb-4" />
        <GrowthStatsSummary :stats="growthStats" />
        <GrowthResultCard :result="latestDetection" />
      </el-col>

      <!-- 右侧显示区域 -->
      <el-col :xs="24" :sm="24" :md="16" :lg="18">
        <GrowthImageDisplay
          :src="currentImage"
          :is-stream="isStream"
          class="mb-4"
          @delete="handleStopDetection"
        />
        <GrowthActionButtons
          :is-camera-active="isCameraActive"
          @upload="handleUpload"
          @start-camera="handleStartCamera"
          @stop-detection="handleStopDetection"
        />
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
  import { ref, reactive, onUnmounted } from 'vue'
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import { ElMessage } from 'element-plus'
  import type { GrowthDetectionItem, GrowthStats } from '@/types/growth-monitoring'
  import { detectGrowth, getCameraStream } from '@/api/growth-monitoring/detect'
  import GrowthControlPanel from './components/GrowthControlPanel.vue'
  import GrowthStatsSummary from './components/GrowthStatsSummary.vue'
  import GrowthImageDisplay from './components/GrowthImageDisplay.vue'
  import GrowthActionButtons from './components/GrowthActionButtons.vue'
  import GrowthResultCard from './components/GrowthResultCard.vue'

  defineOptions({ name: 'GrowthMonitoringDetect' })

  // 状态定义
  const confidence = ref(50)
  const currentImage = ref<string | null>(null)
  const isCameraActive = ref(false)
  const isStream = ref(false)
  
  // 生长状态统计
  const growthStats = reactive<GrowthStats>({
    small: 0,
    normal: 0,
    large: 0
  })

  // 最新检测结果
  const latestDetection = ref<GrowthDetectionItem | null>(null)

  // 重置统计
  const resetStats = () => {
    growthStats.small = 0
    growthStats.normal = 0
    growthStats.large = 0
    latestDetection.value = null
  }

  // 处理上传
  const handleUpload = async (imgData: string) => {
    currentImage.value = imgData
    isStream.value = false
    isCameraActive.value = false
    resetStats()

    try {
      const result = await detectGrowth(imgData)
      updateStats(result.detections)
      
      // 更新最新结果显示 (显示置信度最高的或者第一个)
      if (result.detections.length > 0) {
        // 按置信度排序
        const sorted = [...result.detections].sort((a, b) => b.confidence - a.confidence)
        latestDetection.value = sorted[0]
      }
    } catch (err) {
      console.error('检测失败:', err)
      ElMessage.error('检测失败，请重试')
    }
  }

  // 开启摄像头
  const handleStartCamera = async () => {
    try {
      const streamUrl = await getCameraStream()
      if (!streamUrl) {
        ElMessage.warning('暂未配置摄像头流')
        return
      }
      currentImage.value = streamUrl
      isStream.value = true
      isCameraActive.value = true
      resetStats()
      ElMessage.success('摄像头已开启')
      
      // 模拟实时检测 (每3秒更新一次数据)
      startRealTimeSimulation()
    } catch (err) {
      console.error('无法获取视频流:', err)
      ElMessage.error('无法连接到摄像头')
    }
  }

  let simulationTimer: number | null = null

  const startRealTimeSimulation = () => {
    if (simulationTimer) {
      window.clearInterval(simulationTimer)
      simulationTimer = null
    }
    
    simulationTimer = window.setInterval(async () => {
      if (!isCameraActive.value) {
        if (simulationTimer) window.clearInterval(simulationTimer)
        simulationTimer = null
        return
      }
      // 模拟检测
      try {
        const result = await detectGrowth('stream-frame')
        updateStats(result.detections)
        if (result.detections.length > 0) {
          latestDetection.value = result.detections[0]
        }
      } catch (e) {
        console.error(e)
      }
    }, 3000)
  }

  // 停止检测
  const handleStopDetection = () => {
    currentImage.value = null
    isStream.value = false
    isCameraActive.value = false
    if (simulationTimer) window.clearInterval(simulationTimer)
    simulationTimer = null
    resetStats()
    ElMessage.info('已停止检测')
  }

  // 更新统计
  const updateStats = (detections: GrowthDetectionItem[]) => {
    detections.forEach((det) => {
      if (det.confidence * 100 >= confidence.value) {
        const className = det.class as keyof GrowthStats
        if (growthStats[className] !== undefined) {
          growthStats[className]++
        }
      }
    })
  }

  onUnmounted(() => {
    if (simulationTimer) window.clearInterval(simulationTimer)
    simulationTimer = null
  })
</script>

<style scoped lang="scss">
  .growth-monitoring-detect {
    padding: 20px;

    .page-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 16px 20px;
      margin-bottom: 20px;
      background: var(--el-bg-color);
      border-radius: 8px;
      box-shadow: 0 2px 12px 0 rgb(0 0 0 / 10%);

      .title-section {
        display: flex;
        gap: 12px;
        align-items: center;

        h2 {
          margin: 0;
          font-size: 24px;
          font-weight: 600;
          background: linear-gradient(135deg, #1890ff 0%, #36cfc9 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }
      }
    }

    .mb-4 {
      margin-bottom: 16px;
    }
  }

  // 动画
  .is-loading {
    animation: rotating 2s linear infinite;
  }

  @keyframes rotating {
    from {
      transform: rotate(0deg);
    }

    to {
      transform: rotate(360deg);
    }
  }
</style>
