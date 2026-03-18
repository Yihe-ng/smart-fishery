<template>
  <div class="feeding-page page-container">
    <div class="feeding-layout">
      <section class="main-column">
        <div class="video-wrap">
          <VideoPlayer :src="videoSrc" />
        </div>

        <div class="content-grid">
          <el-card shadow="never" class="config-card">
            <template #header>
              <div class="card-header">
                <span class="font-bold">投喂参数配置</span>
                <ArtSvgIcon icon="ri:settings-4-line" class="text-sky-500" />
              </div>
            </template>
            <el-form :model="config" label-position="top">
              <el-form-item label="饲料系数 (Feed Coefficient)">
                <el-slider
                  v-model="config.feedCoefficient"
                  :min="1.4"
                  :max="1.8"
                  :step="0.1"
                  show-input
                />
              </el-form-item>
              <el-form-item label="投喂频次 (Frequency)">
                <el-input-number v-model="config.frequency" :min="1" :max="8" class="w-full" />
              </el-form-item>
              <el-form-item label="饲料粒径 (Feed Size)">
                <el-select v-model="config.feedSize" class="w-full">
                  <el-option label="1.0mm (幼鱼)" value="1.0mm" />
                  <el-option label="1.5mm (中鱼)" value="1.5mm" />
                  <el-option label="2.0mm (成鱼)" value="2.0mm" />
                </el-select>
              </el-form-item>
              <el-form-item label="模糊 PID 权重预留">
                <el-switch v-model="pidEnabled" active-text="启用自动优化" />
              </el-form-item>
              <el-button type="primary" class="w-full" @click="saveConfig">保存并应用</el-button>
            </el-form>
          </el-card>

          <el-card shadow="never" class="logs-card">
            <template #header>
              <div class="card-header">
                <span class="font-bold">投喂执行日志</span>
                <el-button link type="primary" @click="loadData">刷新</el-button>
              </div>
            </template>
            <el-table :data="logs" border>
              <el-table-column prop="feedTime" label="投喂时间" width="180" />
              <el-table-column prop="amount" label="投喂量(g)" align="center" />
              <el-table-column prop="triggerType" label="触发方式" align="center">
                <template #default="{ row }">
                  <el-tag :type="row.triggerType === 'auto' ? 'primary' : 'info'" size="small">
                    {{ row.triggerType === 'auto' ? '自动' : '手动' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="status" label="状态" align="center">
                <template #default="{ row }">
                  <el-tag :type="row.status === 'completed' ? 'success' : 'warning'" size="small">
                    {{ row.status === 'completed' ? '已完成' : '待处理' }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>

            <div class="quick-feed">
              <div>
                <h4>快速投喂</h4>
                <p>第一阶段仍为 mock 联调，仅生成后端 mock 日志与 AI 预览。</p>
              </div>
              <div class="quick-actions">
                <el-input-number v-model="manualAmount" :min="100" :step="100" class="w-full" />
                <el-button type="success" @click="handleManualFeed">
                  立即投喂 ({{ manualAmount }}g)
                </el-button>
              </div>
            </div>
          </el-card>
        </div>
      </section>

      <aside class="suggestion-column">
        <AISuggestionPanel :pond-id="pondId" />
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { ElMessage } from 'element-plus'
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import { getCameraStream } from '@/api/growth-monitoring/detect'
  import { getFeedingConfig, getFeedingLogs, manualFeeding, updateFeedingConfig } from '@/api/feeding'
  import VideoPlayer from '@/views/dashboard/fishery-console/components/VideoPlayer.vue'
  import AISuggestionPanel from './components/AISuggestionPanel.vue'
  import type { FeedingConfig, FeedingLog } from '@/types/feeding'

  defineOptions({ name: 'FeedingPage' })

  const pondId = 'pond-001'
  const config = reactive<FeedingConfig>({
    feedCoefficient: 1.6,
    frequency: 3,
    feedSize: '2.0mm',
  })
  const pidEnabled = ref(true)
  const manualAmount = ref(500)
  const logs = ref<FeedingLog[]>([])
  const videoSrc = ref('')

  const loadData = async () => {
    try {
      const [cfg, logRes] = await Promise.all([
        getFeedingConfig(),
        getFeedingLogs({ current: 1, size: 10 }),
      ])
      Object.assign(config, cfg)
      logs.value = logRes.list
    } catch (error) {
      console.error('Failed to load feeding data:', error)
      ElMessage.error('投喂 mock 数据加载失败')
    }
  }

  const initVideoStream = async () => {
    try {
      const streamUrl = await getCameraStream()
      videoSrc.value = streamUrl || ''
    } catch (error) {
      console.error('Failed to load camera stream:', error)
      ElMessage.warning('视频加载失败，但 AI 建议栏仍可使用')
    }
  }

  const saveConfig = async () => {
    try {
      await updateFeedingConfig(config)
      ElMessage.success('投喂配置已同步到后端 mock 数据源')
    } catch (error) {
      console.error('Failed to save config:', error)
      ElMessage.error('配置保存失败')
    }
  }

  const handleManualFeed = async () => {
    try {
      await manualFeeding(manualAmount.value)
      ElMessage.success(`已写入 mock 投喂指令 ${manualAmount.value}g`)
      await loadData()
    } catch (error) {
      console.error('Failed to send feeding command:', error)
      ElMessage.error('投喂指令发送失败')
    }
  }

  onMounted(async () => {
    await Promise.allSettled([loadData(), initVideoStream()])
  })
</script>

<style scoped lang="scss">
  .feeding-page {
    padding: 20px;
  }

  .feeding-layout {
    display: grid;
    grid-template-columns: minmax(0, 2fr) minmax(320px, 1fr);
    gap: 16px;
    align-items: stretch;
  }

  .main-column,
  .suggestion-column {
    min-width: 0;
  }

  .main-column {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .video-wrap {
    min-height: 360px;
  }

  .content-grid {
    display: grid;
    grid-template-columns: minmax(280px, 0.9fr) minmax(0, 1.1fr);
    gap: 16px;
  }

  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }

  .config-card,
  .logs-card,
  .suggestion-column {
    min-height: 0;
  }

  .logs-card {
    display: flex;
    flex-direction: column;
  }

  .quick-feed {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 16px;
    padding-top: 16px;

    h4,
    p {
      margin: 0;
    }

    p {
      margin-top: 6px;
      color: var(--el-text-color-secondary);
      line-height: 1.6;
    }
  }

  .quick-actions {
    display: flex;
    flex: 0 0 260px;
    flex-direction: column;
    gap: 10px;
  }

  @media (width <= 1200px) {
    .feeding-layout,
    .content-grid {
      grid-template-columns: 1fr;
    }
  }

  @media (width <= 768px) {
    .quick-feed {
      flex-direction: column;
      align-items: stretch;
    }

    .quick-actions {
      flex-basis: auto;
    }
  }
</style>
