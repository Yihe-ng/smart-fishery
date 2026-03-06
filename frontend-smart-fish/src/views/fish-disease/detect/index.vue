<template>
  <div class="fish-disease-detect">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="title-section">
        <ArtSvgIcon icon="ri:fish-line" style="font-size: 32px; color: #409eff" />
        <h2>智能鱼类病害识别系统</h2>
      </div>
      <el-tag :type="isCameraActive ? 'success' : 'info'" size="large" effect="dark">
        <ArtSvgIcon v-if="isCameraActive" icon="ri:loader-4-line" class="animate-spin mr-1" />
        {{ isCameraActive ? '系统监控中' : '系统待命' }}
      </el-tag>
    </div>

    <el-row :gutter="20">
      <!-- 左侧控制面板 -->
      <el-col :xs="24" :sm="24" :md="8" :lg="6">
        <DetectControlPanel v-model="confidence" class="mb-4" />
        <DetectStatsTable :stats="diseaseStats" />
      </el-col>

      <!-- 右侧显示区域 -->
      <el-col :xs="24" :sm="24" :md="16" :lg="18">
        <DetectImageDisplay
          :src="currentImage"
          :is-stream="isStream"
          class="mb-4"
          @delete="handleStopDetection"
        />
        <DetectActionButtons
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
  import { ref, reactive } from 'vue'
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import { ElMessage } from 'element-plus'
  import type { DiseaseStats } from '@/types/fish-disease'
  import { detectDisease, getCameraStream } from '@/api/fish-disease/detect'
  import DetectControlPanel from './components/DetectControlPanel.vue'
  import DetectStatsTable from './components/DetectStatsTable.vue'
  import DetectImageDisplay from './components/DetectImageDisplay.vue'
  import DetectActionButtons from './components/DetectActionButtons.vue'

  defineOptions({ name: 'FishDiseaseDetect' })

  // 状态定义
  const confidence = ref(50)
  const currentImage = ref<string | null>(null)
  const isCameraActive = ref(false)
  const isStream = ref(false)
  const diseaseStats = reactive<DiseaseStats>({
    烂鳃: 0,
    赤皮: 0,
    肠炎: 0
  })

  // 重置统计
  const resetStats = () => {
    diseaseStats['烂鳃'] = 0
    diseaseStats['赤皮'] = 0
    diseaseStats['肠炎'] = 0
  }

  // 处理上传
  const handleUpload = async (imgData: string) => {
    currentImage.value = imgData
    isStream.value = false
    isCameraActive.value = false
    resetStats()

    try {
      const result = await detectDisease(imgData)
      updateStats(result.detections)
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
    } catch (err) {
      console.error('无法获取视频流:', err)
      ElMessage.error('无法连接到摄像头')
    }
  }

  // 停止检测
  const handleStopDetection = () => {
    currentImage.value = null
    isStream.value = false
    isCameraActive.value = false
    resetStats()
    ElMessage.info('已停止检测')
  }

  // 更新统计
  const updateStats = (detections: Array<{ class: string; confidence: number }>) => {
    detections.forEach((det) => {
      if (det.confidence * 100 >= confidence.value) {
        const className = det.class as keyof DiseaseStats
        if (diseaseStats[className] !== undefined) {
          diseaseStats[className]++
        }
      }
    })
  }
</script>

<style scoped lang="scss">
  .fish-disease-detect {
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
