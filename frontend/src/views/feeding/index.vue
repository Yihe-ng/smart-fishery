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
        <!-- AI投喂建议 - 移至最上方 -->
        <div class="suggestion-section">
          <AISuggestionPanel :pond-id="pondId" @adopt-suggestion="handleAdoptSuggestion" />
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
  import type { FeedingConfig, FeedingLog } from '@/types/feeding'

  defineOptions({ name: 'FeedingPage' })

  // 本地视频源列表
  const videoSources = [
    '/video/VID_20260330_161745.mp4',
    '/video/VID_20260330_161836.mp4',
    '/video/VID_20260330_161930.mp4',
    '/video/VID_20260330_162428.mp4',
    '/video/VID_20260330_163542.mp4',
    '/video/VID_20260330_163804.mp4'
  ]

  const pondId = 'pond-001'
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

  // 处理采纳建议
  const handleAdoptSuggestion = (suggestedAmount: number) => {
    // 将建议投喂量应用到配置中
    // 这里可以根据建议调整饲料系数或记录建议值
    ElMessage.success(`已采纳AI建议：建议投喂量 ${suggestedAmount}g`)
  }

  onMounted(async () => {
    await loadData()
  })
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
      max-height: 45vh;
      min-height: 240px;
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
      flex: 0 0 auto;
      display: flex;
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
        flex: 0 0 60%;
        min-height: 0;
        height: 100%;
        display: flex;
        flex-direction: column;

        :deep(.el-card__header) {
          padding: 6px 10px;
          border-bottom: 1px solid var(--default-border);
          flex-shrink: 0;
        }

        :deep(.el-card__body) {
          padding: 8px 10px;
          flex: 1;
          display: flex;
          flex-direction: column;
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
              color: var(--el-text-color-regular);
              line-height: 1.2;
            }

            // 滑块样式
            :deep(.el-slider) {
              display: flex;
              align-items: center;
              gap: 8px;

              .el-slider__runway {
                flex: 1;
                margin: 0;
              }

              .el-slider__input {
                width: 80px;
                flex-shrink: 0;

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
            border-top: 1px solid var(--default-border);
            margin-top: auto;

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

    // AI投喂建议 - 最上方，向下拉长
    .suggestion-section {
      flex: 1;
      min-height: 280px;
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
      flex: 0 0 auto;
      min-height: 0;
      max-height: 35vh;
      display: flex;
      flex-direction: column;

      :deep(.el-card__header) {
        padding: 8px 12px;
        border-bottom: 1px solid var(--default-border);
        flex-shrink: 0;
      }

      :deep(.el-card__body) {
        padding: 10px 12px;
        flex: 1;
        display: flex;
        flex-direction: column;
        min-height: 0;
      }

      .logs-content {
        max-height: none;
        flex: 1;
        overflow: auto;
        min-height: 0;

        .compact-table {
          font-size: 12px;

          :deep(.el-table__cell) {
            padding: 4px 0;
          }
        }
      }

      .quick-feed {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        margin-top: 10px;
        padding-top: 10px;
        border-top: 1px solid var(--default-border);
        flex-shrink: 0;

        .quick-label {
          font-size: 13px;
          font-weight: 500;
          color: var(--el-text-color-primary);
          white-space: nowrap;
        }

        .quick-actions {
          display: flex;
          align-items: center;
          gap: 8px;
        }
      }
    }
  }

  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
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
  }
</style>
