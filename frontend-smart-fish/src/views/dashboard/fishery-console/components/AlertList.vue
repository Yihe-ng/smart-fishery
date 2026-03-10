<template>
  <el-card shadow="never" class="alert-list-card">
    <template #header>
      <div class="flex-cb alert-header">
        <div class="flex-c gap-2">
          <ArtSvgIcon icon="ri:notification-3-line" class="text-lg text-red-500" />
          <span class="panel-title">实时告警</span>
          <el-tag v-if="criticalCount > 0" type="danger" size="small" effect="light">
            严重 {{ criticalCount }}
          </el-tag>
        </div>
      </div>
    </template>

    <div class="alert-content-wrap">
      <div class="alert-toolbar">
        <el-radio-group
          v-model="activeLevel"
          size="small"
          class="level-filter"
          aria-label="按级别筛选实时告警"
        >
          <el-radio-button v-for="item in levelOptions" :key="item.value" :label="item.value">
            {{ item.label }}
          </el-radio-button>
        </el-radio-group>
      </div>

      <!-- 空状态 -->
      <div v-if="displayedAlerts.length === 0" class="empty-state">
        <div class="empty-icon">
          <ArtSvgIcon icon="ri:checkbox-circle-line" />
        </div>
        <p class="empty-title">系统运行正常</p>
        <p class="empty-desc">暂无告警信息</p>
      </div>

      <!-- 告警列表 -->
      <div
        v-show="displayedAlerts.length > 0"
        class="alert-items"
        :class="{ 'list-hidden': !isListVisible }"
        role="list"
        aria-label="实时告警列表"
        aria-live="polite"
        aria-atomic="false"
      >
        <div class="alert-list-inner" :key="animKey">
          <article
            v-for="(alert, index) in displayedAlerts"
            :key="alert.id"
            class="alert-card"
            :class="[`level-${alert.level}`]"
            :style="{ '--stagger-index': index }"
            role="listitem"
            tabindex="0"
            @keydown.enter="emit('resolve', alert)"
            @keydown.space.prevent="emit('resolve', alert)"
            :aria-label="`${levelTextMap[alert.level]}告警：${alert.title}`"
          >
            <!-- 左侧渐变光条 -->
            <div class="alert-glow-bar" :class="`glow-${alert.level}`">
              <div class="glow-inner"></div>
            </div>
            <!-- 卡片内容 -->
            <div class="alert-card-body">
              <!-- 顶部行：图标 + 标签 + 标题 + 时间 -->
              <div class="alert-top-row">
                <div class="alert-info">
                  <span class="level-icon" :class="`icon-${alert.level}`">
                    <ArtSvgIcon :icon="levelIconMap[alert.level]" />
                  </span>
                  <el-tag size="small" effect="light" :type="levelTagTypeMap[alert.level]">
                    {{ levelTextMap[alert.level] }}
                  </el-tag>
                  <h4 class="alert-title">{{ alert.title }}</h4>
                </div>
                <time class="alert-time">{{ formatTime(alert.createTime) }}</time>
              </div>
              <p class="alert-message">{{ alert.message }}</p>
              <div class="alert-actions">
                <el-button
                  link
                  :type="alert.level === 'critical' ? 'danger' : 'info'"
                  size="small"
                  @click.stop="emit('resolve', alert)"
                >
                  <ArtSvgIcon icon="ri:close-circle-line" class="mr-1" />
                  忽略
                </el-button>
              </div>
            </div>
          </article>
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
  import { computed, ref, watch } from 'vue'
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import type { Alert } from '@/types/alert'

  const props = defineProps<{
    alerts: Alert[]
  }>()

  const emit = defineEmits<{
    resolve: [alert: Alert]
  }>()

  const activeLevel = ref<'all' | Alert['level']>('all')

  // 动画状态机
  const isListVisible = ref(true)
  const animKey = ref(0)
  const displayedAlerts = ref<Alert[]>([])

  // 同步 props.alerts 变化（不走动画，直接更新）
  const isAnimating = ref(false)
  watch(
    () => props.alerts,
    (val) => {
      if (isAnimating.value) return
      displayedAlerts.value =
        activeLevel.value === 'all' ? val : val.filter((a) => a.level === activeLevel.value)
    },
    { immediate: true, deep: true }
  )

  // 切换筛选时：淡出 → 换数据 + 重建 DOM → 淡入
  watch(activeLevel, (level) => {
    isAnimating.value = true
    isListVisible.value = false
    setTimeout(() => {
      displayedAlerts.value =
        level === 'all' ? props.alerts : props.alerts.filter((a) => a.level === level)
      animKey.value++
      isListVisible.value = true
      isAnimating.value = false
    }, 150)
  })

  const criticalCount = computed(() => props.alerts.filter((a) => a.level === 'critical').length)

  const levelOptions = [
    { label: '全部', value: 'all' },
    { label: '严重', value: 'critical' },
    { label: '警告', value: 'warning' },
    { label: '提示', value: 'info' }
  ] as const

  const levelTextMap: Record<string, string> = {
    critical: '严重',
    warning: '警告',
    info: '提示'
  }

  const levelIconMap: Record<string, string> = {
    critical: 'ri:error-warning-fill',
    warning: 'ri:alert-fill',
    info: 'ri:information-fill'
  }

  const levelTagTypeMap: Record<string, 'danger' | 'warning' | 'info' | 'primary' | 'success'> = {
    critical: 'danger',
    warning: 'warning',
    info: 'info'
  }

  const formatTime = (time: string) => {
    if (/^\d{2}:\d{2}$/.test(time)) return time
    const date = new Date(time)
    if (!isNaN(date.getTime())) {
      return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
    }
    return time
  }
</script>

<style scoped lang="scss">
  .alert-list-card {
    display: flex;
    flex-direction: column;
    height: 100%;
    min-height: 0;

    :deep(.el-card__header) {
      padding: 16px;
    }

    :deep(.el-card__body) {
      display: flex;
      flex: 1;
      flex-direction: column;
      min-height: 0;
      padding: 0;
    }

    .alert-header {
      gap: 12px;
    }

    .panel-title {
      font-size: 16px;
      font-weight: 600;
      color: var(--el-text-color-primary);
      letter-spacing: 0.01em;
    }

    .alert-content-wrap {
      display: flex;
      flex: 1;
      flex-direction: column;
      min-height: 0;
      padding-bottom: 6px;
      overflow: hidden;
    }

    .alert-toolbar {
      position: sticky;
      top: 0;
      z-index: 2;
      display: flex;
      align-items: center;
      justify-content: flex-start;
      padding: 10px 16px;
      background: var(--default-box-color);
      border-bottom: 1px solid var(--art-card-border);

      .level-filter {
        :deep(.el-radio-button__inner) {
          font-weight: 500;
          transition:
            background-color 0.2s ease,
            border-color 0.2s ease;
        }
      }
    }

    // 空状态样式
    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 48px 20px;

      .empty-icon {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 64px;
        height: 64px;
        margin-bottom: 16px;
        font-size: 32px;
        color: var(--el-color-success);
        background: var(--el-color-success-light-9);
        border-radius: 50%;
      }

      .empty-title {
        margin: 0 0 4px;
        font-size: 16px;
        font-weight: 600;
        color: var(--el-text-color-primary);
      }

      .empty-desc {
        margin: 0;
        font-size: 14px;
        color: var(--art-gray-500);
      }
    }

    .alert-items {
      position: relative;
      flex: 1;
      min-height: 0;
      overflow: hidden auto;
    }

    .alert-list-inner {
      display: flex;
      flex-direction: column;
      gap: 12px;
      padding: 12px 16px;
    }

    // 告警卡片样式
    .alert-card {
      position: relative;
      display: flex;
      gap: 0;
      padding: 0;
      background: var(--default-box-color);
      border: 1px solid var(--art-card-border);
      border-radius: 12px;
      outline: none;
      box-shadow: 0 2px 8px rgb(0 0 0 / 6%);
      // 只对box-shadow做transition，不干扰move动画的transform
      transition:
        box-shadow 0.25s ease,
        background-color 0.25s ease;

      &:hover,
      &:focus-visible {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgb(0 0 0 / 12%);
      }

      // 左侧光条
      .alert-glow-bar {
        position: relative;
        flex-shrink: 0;
        width: 4px;
        border-radius: 12px 0 0 12px;
        overflow: hidden;

        .glow-inner {
          position: absolute;
          inset: 0;
          opacity: 0.6;
        }
      }

      // 级别颜色
      &.level-critical {
        .alert-glow-bar {
          background: var(--el-color-danger);
          .glow-inner {
            background: linear-gradient(
              180deg,
              var(--el-color-danger) 0%,
              transparent 50%,
              var(--el-color-danger) 100%
            );
            animation: pulse-glow 2s ease-in-out infinite;
          }
        }
        .level-icon {
          color: var(--el-color-danger);
        }
      }

      &.level-warning {
        .alert-glow-bar {
          background: var(--el-color-warning);
          .glow-inner {
            background: var(--el-color-warning);
          }
        }
        .level-icon {
          color: var(--el-color-warning);
        }
      }

      &.level-info {
        .alert-glow-bar {
          background: var(--el-color-primary);
          .glow-inner {
            background: var(--el-color-primary);
          }
        }
        .level-icon {
          color: var(--el-color-primary);
        }
      }

      .alert-card-body {
        flex: 1;
        padding: 14px 16px;
        min-width: 0;
      }

      .alert-top-row {
        display: flex;
        gap: 10px;
        align-items: flex-start;
        justify-content: space-between;
      }

      .alert-info {
        display: flex;
        gap: 8px;
        align-items: center;
        min-width: 0;
      }

      .level-icon {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 22px;
        height: 22px;
        font-size: 16px;
      }

      .type-tag {
        color: var(--el-text-color-secondary);
      }

      .alert-title {
        margin: 0;
        font-size: 15px;
        font-weight: 600;
        line-height: 1.35;
        color: var(--el-text-color-primary);
      }

      .alert-message {
        margin: 10px 0;
        font-size: 14px;
        line-height: 1.6;
        color: var(--art-gray-600);
      }

      .alert-actions {
        display: flex;
        gap: 8px;
        padding-top: 8px;
        border-top: 1px solid var(--art-card-border);
      }

      .alert-time {
        flex-shrink: 0;
        font-size: 13px;
        font-weight: 500;
        font-variant-numeric: tabular-nums;
        color: var(--art-gray-500);
        white-space: nowrap;
      }
    }
  }

  // 暗黑模式
  :global(.dark) .alert-list-card {
    .alert-toolbar {
      background: var(--default-box-color);
      border-bottom: 1px solid rgba(255 255 255 / 0.06);
    }

    .alert-card {
      border-color: rgba(99, 179, 237, 0.18);
      box-shadow:
        0 2px 8px rgb(0 0 0 / 30%),
        inset 0 1px 0 rgba(99, 179, 237, 0.06);

      &:hover,
      &:focus-visible {
        box-shadow:
          0 8px 24px rgb(0 0 0 / 40%),
          0 0 0 1px rgba(99, 179, 237, 0.25);
      }

      .alert-actions {
        border-top-color: rgba(255 255 255 / 0.06);
      }

      // 每个级别各自控制背景，基色统一为 #1e3a52
      &.level-critical {
        background: linear-gradient(
          135deg,
          color-mix(in oklch, var(--el-color-danger) 12%, #1e3a52) 0%,
          #1e3a52 100%
        );
      }

      &.level-warning {
        background: linear-gradient(
          135deg,
          color-mix(in oklch, var(--el-color-warning) 10%, #1e3a52) 0%,
          #1e3a52 100%
        );
      }

      &.level-info {
        background: linear-gradient(
          135deg,
          color-mix(in oklch, var(--el-color-primary) 10%, #1e3a52) 0%,
          #1e3a52 100%
        );
      }

      // 无级别时的默认背景（放在最后作为 fallback）
      &:not(.level-critical):not(.level-warning):not(.level-info) {
        background: #1e3a52;
      }
    }

    .empty-state .empty-icon {
      background: color-mix(in oklch, var(--el-color-success) 15%, transparent);
    }
  }

  // 脉动动画
  @keyframes pulse-glow {
    0%,
    100% {
      opacity: 0.4;
      transform: scaleY(1);
    }
    50% {
      opacity: 0.8;
      transform: scaleY(1.2);
    }
  }

  // 列表容器淡出/淡入（用 animation 避免 class 移除时的瞬间跳变）
  .alert-items {
    &.list-hidden {
      animation: list-fade-out 0.15s ease-in forwards;
    }
    &:not(.list-hidden) {
      animation: list-fade-in 0.2s ease-out forwards;
    }
  }
  @keyframes list-fade-out {
    to {
      opacity: 0;
      transform: translateY(4px);
    }
  }
  @keyframes list-fade-in {
    from {
      opacity: 0;
      transform: translateY(4px);
    }
    to {
      opacity: 1;
      transform: none;
    }
  }
  // 卡片入场：纯 CSS animation，不依赖 Vue 过渡系统
  .alert-list-inner .alert-card {
    animation: card-enter 0.35s cubic-bezier(0.16, 1, 0.3, 1) both;
    animation-delay: calc(min(var(--stagger-index), 3) * 40ms);
  }
  @keyframes card-enter {
    from {
      opacity: 0;
      transform: translateY(16px) scale(0.97);
    }
    to {
      opacity: 1;
      transform: none;
    }
  }

  // 空状态淡入动画
  .empty-state {
    animation: empty-fade-in 0.4s ease-out;
  }
</style>
