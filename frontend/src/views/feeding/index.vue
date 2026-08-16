<template>
  <div class="feeding-page">
    <el-row :gutter="16" class="feeding-layout">
      <!-- 左侧：55% -->
      <el-col :span="13" class="left-column">
        <!-- 视频播放器 - 16:9比例，max-height: 45vh -->
        <div class="video-section">
          <VideoPlayer :sources="videoSources" />
        </div>

        <!-- 底部区域：天气 + 参数配置 -->
        <div class="bottom-section">
          <!-- 天气卡片 - 左侧 -->
          <div class="weather-section-left">
            <WeatherCard />
          </div>

          <!-- 投喂参数配置 - 右侧 -->
          <el-card shadow="never" class="config-card">
            <template #header>
              <div class="card-header">
                <span class="font-bold">投喂参数配置</span>
                <ArtSvgIcon icon="ri:settings-4-line" class="text-sky-500" />
              </div>
            </template>
            <div class="config-form">
              <!-- 饲料系数 -->
              <div class="form-item">
                <label class="form-label">饲料系数</label>
                <el-slider
                  v-model="config.feedCoefficient"
                  :min="1.4"
                  :max="1.8"
                  :step="0.1"
                  show-input
                  :show-input-controls="false"
                  input-size="small"
                />
              </div>
              <!-- 频次和粒径 -->
              <div class="form-row">
                <div class="form-item half">
                  <label class="form-label">投喂频次</label>
                  <el-input-number
                    v-model="config.frequency"
                    :min="1"
                    :max="8"
                    class="w-full"
                    size="small"
                  />
                </div>
                <div class="form-item half">
                  <label class="form-label">饲料粒径</label>
                  <el-select v-model="config.feedSize" class="w-full" size="small">
                    <el-option label="1.0mm (幼鱼)" value="1.0mm" />
                    <el-option label="1.5mm (中鱼)" value="1.5mm" />
                    <el-option label="2.0mm (成鱼)" value="2.0mm" />
                  </el-select>
                </div>
              </div>
              <!-- 开关和按钮 -->
              <div class="form-actions">
                <el-switch v-model="pidEnabled" active-text="启用模糊PID自动优化" size="small" />
                <el-button type="primary" size="small" @click="saveConfig">保存并应用</el-button>
              </div>
            </div>
          </el-card>
        </div>
      </el-col>

      <!-- 右侧：45% -->
      <el-col :span="11" class="right-column">
        <!-- 生长与投喂建议 - 置顶主位；独立的“最近生长识别参考”卡片已合并进本卡片（方案 §8.1） -->
        <div class="suggestion-section">
          <AISuggestionPanel :pond-id="pondId" :current-index="currentIndex" />
        </div>

        <!-- 投喂执行日志 - 中间位置 -->
        <el-card shadow="never" class="logs-card">
          <template #header>
            <div class="card-header">
              <span class="font-bold">投喂执行日志</span>
              <el-button link type="primary" @click="loadData">刷新</el-button>
            </div>
          </template>
          <div class="logs-content">
            <el-table :data="logs" border size="small" class="compact-table">
              <el-table-column prop="feedTime" label="时间" width="140" />
              <el-table-column prop="amount" label="量(g)" align="center" width="70" />
              <el-table-column prop="triggerType" label="方式" align="center" width="60">
                <template #default="{ row }">
                  <el-tag :type="row.triggerType === 'auto' ? 'primary' : 'info'" size="small">
                    {{ row.triggerType === 'auto' ? '自动' : '手动' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="status" label="状态" align="center" width="60">
                <template #default="{ row }">
                  <el-tag :type="row.status === 'completed' ? 'success' : 'warning'" size="small">
                    {{ row.status === 'completed' ? '完成' : '待处理' }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>

          <!-- 快速投喂 -->
          <div class="quick-feed">
            <span class="quick-label">快速投喂</span>
            <div class="quick-actions">
              <el-input-number v-model="manualAmount" :min="100" :step="100" size="small" />
              <el-button type="success" size="small" @click="handleManualFeed">
                投喂 {{ manualAmount }}g
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
  import { ElMessage } from 'element-plus'
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import {
    getFeedingConfig,
    getFeedingLogs,
    manualFeeding,
    updateFeedingConfig
  } from '@/api/feeding'
  import VideoPlayer from '@/views/dashboard/fishery-console/components/VideoPlayer.vue'
  import AISuggestionPanel from './components/AISuggestionPanel.vue'
  import WeatherCard from './components/WeatherCard.vue'
  import { useDemoFrameSnapshot } from '@/composables/use-demo-frame-snapshot'
  import { getVideoList } from '@/api/video'
  import type { FeedingConfig, FeedingLog } from '@/types/feeding'

  defineOptions({ name: 'FeedingPage' })

  // 动态视频源列表（从后端 API 获取）
  const videoSources = ref<string[]>([])

  const { snapshot } = useDemoFrameSnapshot()
  const pondId = computed(() => snapshot.pondId)
  const currentIndex = computed(() => snapshot.currentIndex)
  const config = reactive<FeedingConfig>({
    feedCoefficient: 1.6,
    frequency: 3,
    feedSize: '2.0mm'
  })
  const pidEnabled = ref(true)
  const manualAmount = ref(500)
  const logs = ref<FeedingLog[]>([])

  const loadData = async () => {
    try {
      const [cfg, logRes] = await Promise.all([
        getFeedingConfig(),
        getFeedingLogs({ current: 1, size: 10 })
      ])
      Object.assign(config, cfg)
      logs.value = logRes.list
    } catch (error) {
      console.error('Failed to load feeding data:', error)
      ElMessage.error('投喂数据加载失败')
    }
  }

  const saveConfig = async () => {
    try {
      await updateFeedingConfig(config)
      ElMessage.success('投喂配置已保存')
    } catch (error) {
      console.error('Failed to save config:', error)
      ElMessage.error('配置保存失败')
    }
  }

  const handleManualFeed = async () => {
    try {
      await manualFeeding(manualAmount.value)
      ElMessage.success(`已执行投喂 ${manualAmount.value}g`)
      await loadData()
    } catch (error) {
      console.error('Failed to send feeding command:', error)
      ElMessage.error('投喂指令发送失败')
    }
  }

  // 订阅投喂执行状态（投喂开始/完成）——后端经 WebSocket 广播给前端客户端
  let feedingWs: WebSocket | null = null
  const subscribeFeedingStatus = () => {
    const wsUrl = `ws://${window.location.hostname}:8000/ws/device/feeding-client`
    try {
      feedingWs = new WebSocket(wsUrl)
      feedingWs.onmessage = (ev) => {
        let msg: { type?: string; data?: { amount?: number } }
        try {
          msg = JSON.parse(ev.data as string)
        } catch {
          return
        }
        const amount = msg.data?.amount
        if (msg.type === 'feeding_status') {
          ElMessage.info(`投喂开始：${amount ?? ''}g`)
        } else if (msg.type === 'feeding_complete') {
          ElMessage.success(`投喂完成：${amount ?? ''}g`)
        }
      }
      feedingWs.onclose = () => {
        feedingWs = null
      }
    } catch {
      feedingWs = null
    }
  }

  const unsubscribeFeedingStatus = () => {
    if (feedingWs) {
      feedingWs.close()
      feedingWs = null
    }
  }

  const fetchVideoList = async () => {
    try {
      const sources = await getVideoList()
      videoSources.value = sources
    } catch {
      // http 层已展示错误提示，此处仅降级为空列表
      videoSources.value = []
    }
  }

  onMounted(async () => {
    fetchVideoList()
    await loadData()
    subscribeFeedingStatus()
  })

  onUnmounted(unsubscribeFeedingStatus)
</script>

<style scoped lang="scss">
  .feeding-page {
    height: 100vh;
    padding: 16px;
    overflow: hidden;
    background-color: var(--art-bg-color);
  }

  .feeding-layout {
    height: 100%;

    :deep(.el-col) {
      height: 100%;
    }
  }

  // 左侧列
  .left-column {
    display: flex;
    flex-direction: column;
    gap: 10px;
    height: 100%;
    min-height: 0;

    .video-section {
      flex: 0 0 auto;
      min-height: 240px;
      max-height: 45vh;
      overflow: hidden;

      :deep(.video-player-card) {
        height: 100%;

        :deep(.el-card__body) {
          height: calc(100% - 57px);
          padding: 12px;
        }

        .video-container {
          width: 100%;
          height: 100%;
          aspect-ratio: 16/9;
        }
      }
    }

    // 底部区域：天气 + 参数配置
    .bottom-section {
      display: flex;
      flex: 0 0 auto;
      gap: 10px;
      min-height: 180px;
      max-height: 200px;

      // 天气卡片 - 左侧 40%
      .weather-section-left {
        flex: 0 0 40%;
        min-width: 180px;
        max-width: 300px;
        height: 100%;

        :deep(.weather-card-compact) {
          height: 100%;
        }
      }

      // 投喂参数配置 - 右侧 60%
      .config-card {
        display: flex;
        flex: 0 0 60%;
        flex-direction: column;
        height: 100%;
        min-height: 0;

        :deep(.el-card__header) {
          flex-shrink: 0;
          padding: 6px 10px;
          border-bottom: 1px solid var(--default-border);
        }

        :deep(.el-card__body) {
          display: flex;
          flex: 1;
          flex-direction: column;
          padding: 8px 10px;
          overflow: visible;
        }

        .config-form {
          display: flex;
          flex-direction: column;
          gap: 6px;
          height: 100%;

          .form-item {
            display: flex;
            flex-direction: column;
            gap: 2px;

            &.half {
              flex: 1;
            }

            .form-label {
              font-size: 11px;
              line-height: 1.2;
              color: var(--el-text-color-regular);
            }

            // 滑块样式
            :deep(.el-slider) {
              display: flex;
              gap: 8px;
              align-items: center;

              .el-slider__runway {
                flex: 1;
                margin: 0;
              }

              .el-slider__input {
                flex-shrink: 0;
                width: 80px;

                .el-input__inner {
                  padding: 0 8px;
                  text-align: center;
                }
              }
            }
          }

          // 双列行
          .form-row {
            display: flex;
            gap: 12px;
          }

          // 操作行
          .form-actions {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding-top: 6px;
            margin-top: auto;
            border-top: 1px solid var(--default-border);

            :deep(.el-switch__label) {
              font-size: 11px;
            }
          }
        }
      }
    }
  }

  // 右侧列
  .right-column {
    display: flex;
    flex-direction: column;
    gap: 10px;
    height: 100%;
    min-height: 0;

    // 生长与投喂建议 - 最上方，向下拉长
    .suggestion-section {
      flex: 1;
      min-height: 230px;
      max-height: none;
      overflow: hidden;

      :deep(.ai-suggestion-panel) {
        height: 100%;

        :deep(.el-card__body) {
          height: calc(100% - 50px);
        }
      }
    }

    // 投喂执行日志 - 固定高度
    .logs-card {
      display: flex;
      flex: 0 0 auto;
      flex-direction: column;
      min-height: 0;
      max-height: 30vh;

      :deep(.el-card__header) {
        flex-shrink: 0;
        padding: 8px 12px;
        border-bottom: 1px solid var(--default-border);
      }

      :deep(.el-card__body) {
        display: flex;
        flex: 1;
        flex-direction: column;
        min-height: 0;
        padding: 10px 12px;
      }

      .logs-content {
        flex: 1;
        min-height: 0;
        max-height: none;
        overflow: auto;

        .compact-table {
          font-size: 12px;

          :deep(.el-table__cell) {
            padding: 4px 0;
          }
        }
      }

      .quick-feed {
        display: flex;
        flex-shrink: 0;
        gap: 10px;
        align-items: center;
        justify-content: space-between;
        padding-top: 10px;
        margin-top: 10px;
        border-top: 1px solid var(--default-border);

        .quick-label {
          font-size: 13px;
          font-weight: 500;
          color: var(--el-text-color-primary);
          white-space: nowrap;
        }

        .quick-actions {
          display: flex;
          gap: 8px;
          align-items: center;
        }
      }
    }
  }

  .card-header {
    display: flex;
    gap: 12px;
    align-items: center;
    justify-content: space-between;
  }

  // 响应式适配
  @media (width <= 1200px) {
    .feeding-page {
      height: auto;
      overflow: auto;
    }

    .feeding-layout {
      :deep(.el-col) {
        width: 100% !important;
        height: auto;
      }
    }

    .left-column,
    .right-column {
      height: auto;
    }

    .right-column {
      .suggestion-section,
      .logs-card {
        flex: initial;
        max-height: none;
      }
    }
  }
</style>
