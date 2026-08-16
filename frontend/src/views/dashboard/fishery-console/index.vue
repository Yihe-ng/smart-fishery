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
      <VideoPlayer class="area-video dashboard-card-base dashboard-fill" :sources="videoSources" />

      <GrowthRecognitionSummaryCard
        class="area-growth dashboard-card-base dashboard-fill"
        :pond-id="currentPondId"
      />

      <FeedingPanel class="area-feed dashboard-card-base dashboard-fill" />

      <el-card shadow="never" class="decision-card area-status dashboard-card-base dashboard-fill">
        <template #header>
          <div class="flex-cb">
            <div class="decision-title">
              <ArtSvgIcon icon="ri:file-list-3-line" class="decision-title-icon" />
              <span class="font-bold">投喂决策输入摘要</span>
            </div>
            <el-tag type="info" effect="plain" size="small">辅助判断</el-tag>
          </div>
        </template>

        <div class="decision-list">
          <div v-for="item in decisionInputs" :key="item.label" class="decision-item">
            <div class="decision-icon" :class="item.status">
              <ArtSvgIcon :icon="item.icon" />
            </div>
            <div class="decision-copy">
              <div class="decision-label">{{ item.label }}</div>
              <div class="decision-value">{{ item.value }}</div>
            </div>
            <el-tag :type="item.tagType" effect="plain" size="small">{{ item.tag }}</el-tag>
          </div>
        </div>

        <p class="decision-note">
          投喂辅助建议仍结合水质、告警、设备状态和规则数据判断，最近生长识别仅作为鱼体规格参考。
        </p>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { computed, onMounted, ref } from 'vue'
  import { ElMessage } from 'element-plus'

  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import FeedingPanel from './components/FeedingPanel.vue'
  import VideoPlayer from './components/VideoPlayer.vue'
  import GrowthRecognitionSummaryCard from '@/components/business/GrowthRecognitionSummaryCard.vue'

  import { getDashboardFrame } from '@/api/water-quality'
  import { getVideoList } from '@/api/video'
  import { useDemoFrameSnapshot } from '@/composables/use-demo-frame-snapshot'
  import { useGrowthSummaryHydration } from '@/composables/useGrowthSummaryHydration'
  import {
    DEFAULT_GROWTH_POND_ID,
    useGrowthRecognitionStore
  } from '@/store/modules/growth-recognition'
  import type { DashboardFrameResponse } from '@/types/water-quality'

  // 动态视频源列表（从后端 API 获取）
  const videoSources = ref<string[]>([])

  const lastUpdateTime = ref('--:--:--')
  const currentFrameIndex = ref(0)
  const nextFrameIndex = ref(0)
  const dashboardFrame = ref<DashboardFrameResponse | null>(null)
  const { setSnapshot } = useDemoFrameSnapshot()
  const growthRecognitionStore = useGrowthRecognitionStore()

  const currentPondId = computed(
    () =>
      dashboardFrame.value?.pondId ??
      dashboardFrame.value?.waterQuality?.pondId ??
      DEFAULT_GROWTH_POND_ID
  )
  // 本地缓存为空或库里有更新记录时，从数据库恢复最近识别摘要
  useGrowthSummaryHydration(currentPondId)

  const latestGrowthSummary = computed(() =>
    growthRecognitionStore.getLatestSummary(currentPondId.value)
  )

  const growthReferenceState = computed(() => {
    if (!latestGrowthSummary.value) return { tag: '暂无结果', tagType: 'info' as const }
    if (growthRecognitionStore.isSummaryExpired(latestGrowthSummary.value)) {
      return { tag: '可能过期', tagType: 'warning' as const }
    }
    return { tag: '已更新', tagType: 'success' as const }
  })

  const decisionInputs = computed(() => {
    const waterStatus = dashboardFrame.value?.waterQuality?.status
    const alerts = dashboardFrame.value?.alerts ?? []
    const devices = dashboardFrame.value?.devices ?? []
    const offlineDevices = devices.filter((device) => device.status !== 'online')
    const hasHighRiskAlert = alerts.some(
      (alert) => alert.level === 'critical' && alert.status === 'pending'
    )

    return [
      {
        label: '水质状态',
        value:
          waterStatus === 'normal' ? '当前水质正常' : waterStatus ? '存在水质异常' : '暂无水质快照',
        tag: waterStatus === 'normal' ? '正常' : waterStatus ? '异常' : '待更新',
        tagType:
          waterStatus === 'normal'
            ? ('success' as const)
            : waterStatus
              ? ('warning' as const)
              : ('info' as const),
        icon: 'ri:drop-line',
        status: waterStatus === 'normal' ? 'normal' : 'warning'
      },
      {
        label: '告警状态',
        value: hasHighRiskAlert ? '存在高风险告警' : '无高风险告警',
        tag: hasHighRiskAlert ? '需关注' : '稳定',
        tagType: hasHighRiskAlert ? ('danger' as const) : ('success' as const),
        icon: 'ri:alarm-warning-line',
        status: hasHighRiskAlert ? 'danger' : 'normal'
      },
      {
        label: '设备状态',
        value: offlineDevices.length ? `${offlineDevices.length} 台设备异常` : '关键设备在线',
        tag: offlineDevices.length ? '异常' : '在线',
        tagType: offlineDevices.length ? ('warning' as const) : ('success' as const),
        icon: 'ri:router-line',
        status: offlineDevices.length ? 'warning' : 'normal'
      },
      {
        label: '最近生长识别',
        value: latestGrowthSummary.value
          ? `${latestGrowthSummary.value.detectedCount} 尾样本，平均 ${latestGrowthSummary.value.avgWeightG.toFixed(1)}g`
          : '暂无最近识别结果',
        tag: growthReferenceState.value.tag,
        tagType: growthReferenceState.value.tagType,
        icon: 'ri:scales-3-line',
        status: growthReferenceState.value.tagType === 'success' ? 'normal' : 'warning'
      }
    ]
  })

  const applyFrame = (frame: DashboardFrameResponse) => {
    dashboardFrame.value = frame
    currentFrameIndex.value = frame.index
    nextFrameIndex.value = frame.nextIndex
    lastUpdateTime.value = frame.collectTime ?? '--'
    setSnapshot({
      currentIndex: frame.index,
      pondId: frame.pondId ?? frame.waterQuality?.pondId,
      collectTime: frame.collectTime ?? undefined
    })
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

  const fetchVideoList = async () => {
    try {
      const sources = await getVideoList()
      if (sources.length === 0) {
        console.warn('视频列表为空')
      }
      videoSources.value = sources
    } catch {
      // http 层已展示错误提示，此处仅降级为空列表
      videoSources.value = []
    }
  }

  onMounted(() => {
    fetchVideoList()
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
      /* stylelint-disable declaration-block-no-redundant-longhand-properties */
      grid-template-areas:
        'video video growth'
        'feed feed status';
      grid-template-rows: clamp(300px, 37vh, 360px) clamp(360px, 36vh, 420px);
      grid-template-columns: 1.12fr 0.84fr minmax(380px, 1.08fr);
      /* stylelint-enable declaration-block-no-redundant-longhand-properties */
      gap: 20px;
      align-items: stretch;
    }

    .area-video {
      grid-area: video;
    }

    .area-growth {
      grid-area: growth;
    }

    .area-feed {
      grid-area: feed;
    }

    .area-status {
      grid-area: status;
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

    .section-title {
      padding-left: 10px;
      margin-bottom: 12px;
      font-size: 16px;
      font-weight: 700;
      color: var(--el-text-color-primary);
      border-left: 4px solid var(--el-color-primary);
    }

    .decision-card {
      display: flex;
      flex-direction: column;
      overflow: hidden;

      :deep(.el-card__header) {
        flex-shrink: 0;
        border-bottom: 1px solid var(--art-card-border);
      }

      :deep(.el-card__body) {
        display: flex;
        flex: 1;
        flex-direction: column;
        gap: 12px;
        height: calc(100% - 57px);
        min-height: 0;
        padding: 16px;
        overflow: hidden;
      }

      .decision-title {
        display: flex;
        gap: 8px;
        align-items: center;
        min-width: 0;
      }

      .decision-title-icon {
        flex-shrink: 0;
        font-size: 18px;
        color: var(--el-color-primary);
      }

      .decision-list {
        display: flex;
        flex: 1;
        flex-direction: column;
        gap: 10px;
        min-height: 0;
        padding-right: 4px;
        overflow-y: auto;
      }

      .decision-item {
        display: grid;
        grid-template-columns: 34px minmax(0, 1fr) auto;
        gap: 10px;
        align-items: center;
        padding: 10px;
        background: var(--art-hover-color);
        border-radius: 8px;
      }

      .decision-icon {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 34px;
        height: 34px;
        border-radius: 8px;

        &.normal {
          color: var(--el-color-success);
          background: color-mix(in srgb, var(--el-color-success) 10%, transparent);
        }

        &.warning {
          color: var(--el-color-warning);
          background: color-mix(in srgb, var(--el-color-warning) 10%, transparent);
        }

        &.danger {
          color: var(--el-color-danger);
          background: color-mix(in srgb, var(--el-color-danger) 10%, transparent);
        }
      }

      .decision-copy {
        min-width: 0;
      }

      .decision-label {
        margin-bottom: 2px;
        font-size: 12px;
        color: var(--el-text-color-secondary);
      }

      .decision-value {
        overflow: hidden;
        font-size: 14px;
        font-weight: 700;
        color: var(--el-text-color-primary);
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .decision-note {
        flex-shrink: 0;
        padding: 10px 12px;
        margin: 0;
        font-size: 12px;
        line-height: 1.6;
        color: var(--el-text-color-secondary);
        background: var(--default-bg-color);
        border: 1px dashed var(--art-card-border);
        border-radius: 8px;
      }
    }

    @media (width <= 1200px) {
      .dashboard-grid {
        grid-template:
          'video video' auto
          'growth status' auto
          'feed feed' auto
          / 1fr 1fr;
      }
    }

    @media (width <= 768px) {
      .dashboard-grid {
        grid-template:
          'video' auto
          'growth' auto
          'feed' auto
          'status' auto
          / 1fr;
      }
    }
  }

  :global(.dark) .fishery-dashboard {
    .dashboard-panel {
      border-color: rgb(99 179 237 / 10%);
      box-shadow: 0 2px 12px rgb(0 0 0 / 50%);

      &:hover {
        border-color: rgb(99 179 237 / 20%);
        box-shadow: 0 4px 20px rgb(14 165 233 / 12%);
      }
    }

    .decision-card {
      :deep(.el-card__header) {
        border-bottom: 1px solid rgb(99 179 237 / 10%);
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
      border-color: rgb(99 179 237 / 10%);
      box-shadow: 0 2px 12px rgb(0 0 0 / 50%);

      &:hover {
        border-color: rgb(99 179 237 / 20%);
        box-shadow: 0 4px 20px rgb(14 165 233 / 12%);
      }
    }
  }
</style>
