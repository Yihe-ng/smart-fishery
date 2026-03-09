<template>
  <el-card shadow="never" class="alert-list-card">
    <template #header>
      <div class="flex-cb alert-header">
        <div class="flex-c gap-2">
          <el-badge :value="alerts.length" :hidden="alerts.length === 0" class="alert-badge">
            <ArtSvgIcon icon="ri:notification-3-line" class="text-lg text-red-500" />
          </el-badge>
          <span class="panel-title">实时告警</span>
          <el-tag v-if="criticalCount > 0" type="danger" size="small" effect="light"
            >严重 {{ criticalCount }}</el-tag
          >
        </div>
        <el-button
          link
          class="header-toggle-btn"
          :aria-label="isExpanded ? '收起告警列表' : '展开告警列表'"
          @click="isExpanded = !isExpanded"
        >
          {{ isExpanded ? '收起' : '展开' }}
          <ArtSvgIcon :icon="isExpanded ? 'ri:arrow-up-s-line' : 'ri:arrow-down-s-line'" />
        </el-button>
      </div>
    </template>

    <Transition name="panel-fade-slide" mode="out-in">
      <div v-show="isExpanded" class="alert-content-wrap">
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

        <div v-if="filteredAlerts.length === 0" class="py-6 text-center text-g-500 text-sm"
          >暂无告警信息</div
        >

        <div
          v-else
          class="alert-items"
          role="list"
          aria-label="实时告警列表"
          aria-live="polite"
          aria-atomic="false"
        >
          <TransitionGroup name="alert-fade" tag="div" move-class="alert-fade-move" appear>
            <article
              v-for="alert in filteredAlerts"
              :key="alert.id"
              class="alert-item"
              :class="[`level-${alert.level}`, `type-${alert.type}`]"
              role="listitem"
              tabindex="0"
              @keydown.enter="emit('view', alert)"
              @keydown.space.prevent="emit('view', alert)"
              :aria-label="`${levelTextMap[alert.level]}告警：${alert.title}`"
            >
              <div class="alert-accent" :class="`accent-${alert.level}`"></div>

              <div class="alert-main">
                <div class="alert-top-row">
                  <div class="title-wrap">
                    <el-tag size="small" effect="light" :type="levelTagTypeMap[alert.level]">
                      {{ levelTextMap[alert.level] }}
                    </el-tag>
                    <el-tag size="small" effect="plain" class="type-tag">
                      {{ typeTextMap[alert.type] }}
                    </el-tag>
                    <h4 class="title">{{ alert.title }}</h4>
                  </div>
                  <time class="time">{{ formatTime(alert.createTime) }}</time>
                </div>

                <p class="message">{{ alert.message }}</p>

                <div class="alert-actions">
                  <el-button link type="primary" size="small" @click.stop="emit('view', alert)">
                    查看详情
                  </el-button>
                  <el-button
                    link
                    :type="alert.level === 'critical' ? 'danger' : 'info'"
                    size="small"
                    @click.stop="emit('resolve', alert)"
                  >
                    忽略告警
                  </el-button>
                </div>
              </div>
            </article>
          </TransitionGroup>
        </div>
      </div>
    </Transition>
  </el-card>
</template>

<script setup lang="ts">
  import { computed, ref } from 'vue'
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import type { Alert } from '@/types/alert'

  const props = defineProps<{
    alerts: Alert[]
  }>()

  const emit = defineEmits<{
    view: [alert: Alert]
    resolve: [alert: Alert]
  }>()

  const isExpanded = ref(true)
  const activeLevel = ref<'all' | Alert['level']>('all')

  const levelOptions = [
    { label: '全部', value: 'all' },
    { label: '严重', value: 'critical' },
    { label: '警告', value: 'warning' },
    { label: '提示', value: 'info' }
  ] as const

  const levelTextMap: Record<Alert['level'], string> = {
    critical: '严重',
    warning: '警告',
    info: '提示'
  }

  const levelTagTypeMap: Record<Alert['level'], 'danger' | 'warning' | 'info'> = {
    critical: 'danger',
    warning: 'warning',
    info: 'info'
  }

  const typeTextMap: Record<Alert['type'], string> = {
    water_quality: '水质异常',
    device_offline: '设备状态',
    disease_detected: '病害识别'
  }

  const criticalCount = computed(
    () => props.alerts.filter((item) => item.level === 'critical').length
  )

  const filteredAlerts = computed(() => {
    if (activeLevel.value === 'all') return props.alerts
    return props.alerts.filter((item) => item.level === activeLevel.value)
  })

  const formatTime = (time: string) => {
    // 如果时间已经是 HH:mm 格式，直接返回
    if (/^\d{2}:\d{2}$/.test(time)) return time

    // 尝试解析日期
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

    .header-toggle-btn {
      min-height: 32px;
    }

    .alert-content-wrap {
      display: flex;
      flex: 1;
      flex-direction: column;
      min-height: 0;
      padding-bottom: 6px;
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
          transition: all 0.2s ease;
        }

        :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
          transform: translateY(-1px);
        }
      }
    }

    .alert-items {
      position: relative;
      flex: 1;
      min-height: 0;
      overflow: hidden auto;
    }

    .alert-item {
      position: relative;
      display: flex;
      gap: 12px;
      padding: 12px 16px;
      border-bottom: 1px solid var(--art-border-color);
      outline: none;
      transition: background-color 0.2s ease;

      &:last-child {
        border-bottom: none;
      }

      &:hover,
      &:focus-visible {
        background-color: var(--art-hover-color);
      }

      .alert-accent {
        flex-shrink: 0;
        width: 4px;
        border-radius: 999px;

        &.accent-critical {
          background: var(--el-color-danger);
        }

        &.accent-warning {
          background: var(--el-color-warning);
        }

        &.accent-info {
          background: var(--el-color-primary);
        }
      }

      .alert-main {
        flex: 1;
        min-width: 0;
      }

      .alert-top-row {
        display: flex;
        gap: 10px;
        align-items: flex-start;
        justify-content: space-between;
      }

      .title-wrap {
        display: flex;
        gap: 8px;
        align-items: center;
        min-width: 0;
      }

      .type-tag {
        color: var(--el-text-color-secondary);
      }

      .title {
        margin: 0;
        font-size: 15px;
        font-weight: 600;
        line-height: 1.35;
        color: var(--el-text-color-primary);
      }

      .message {
        margin: 8px 0;
        font-size: 14px;
        line-height: 1.6;
        color: var(--art-gray-600);
      }

      .alert-actions {
        display: flex;
        gap: 8px;
      }

      &.level-critical {
        background-color: var(--el-color-danger-light-9);
      }

      &.level-warning {
        background-color: var(--el-color-warning-light-9);
      }

      .time {
        font-size: 13px;
        font-weight: 500;
        font-variant-numeric: tabular-nums;
        color: var(--art-gray-500);
        white-space: nowrap;
      }
    }
  }

  :global(.dark) .alert-list-card {
    .alert-toolbar {
      background: var(--default-box-color);
      border-bottom: 1px solid rgba(255 255 255 / 0.06);
    }

    .alert-item {
      &.level-critical {
        background-color: color-mix(in oklch, var(--el-color-danger) 12%, transparent);
      }
      &.level-warning {
        background-color: color-mix(in oklch, var(--el-color-warning) 12%, transparent);
      }
      &.level-info {
        background-color: color-mix(in oklch, var(--el-color-primary) 12%, transparent);
      }

      &:hover,
      &:focus-visible {
        background-color: var(--art-hover-color);
      }
    }
  }

  .alert-fade-enter-active,
  .alert-fade-leave-active {
    transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  }

  .alert-fade-move {
    transition: transform 0.35s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  }

  .alert-fade-leave-active {
    position: absolute;
    z-index: 0;
    width: calc(100% - 32px);
  }

  .alert-fade-enter-from,
  .alert-fade-leave-to {
    opacity: 0;
    transform: translateY(8px) scale(0.97);
  }

  .alert-fade-leave-to {
    transform: translateX(16px) scale(0.96);
  }

  .panel-fade-slide-enter-active,
  .panel-fade-slide-leave-active {
    transition: all 0.2s ease;
  }

  .panel-fade-slide-enter-from,
  .panel-fade-slide-leave-to {
    opacity: 0;
    transform: translateY(-4px);
  }

  @media (width <= 768px) {
    .alert-list-card {
      .alert-toolbar {
        overflow-x: auto;

        .level-filter {
          min-width: max-content;
        }
      }

      .alert-item {
        padding: 10px 12px;

        .alert-top-row {
          flex-direction: column;
          align-items: flex-start;
        }

        .time {
          padding-left: 2px;
        }

        .alert-actions {
          justify-content: flex-end;
          width: 100%;
        }
      }
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .alert-fade-move,
    .alert-fade-enter-active,
    .alert-fade-leave-active,
    .panel-fade-slide-enter-active,
    .panel-fade-slide-leave-active,
    .alert-item,
    .level-filter :deep(.el-radio-button__inner) {
      transition: none;
    }
  }
</style>
