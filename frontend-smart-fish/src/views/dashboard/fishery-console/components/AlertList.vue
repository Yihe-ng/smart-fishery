<template>
  <el-card shadow="never" class="alert-list-card">
    <template #header>
      <div class="flex-cb">
        <div class="flex-c gap-2">
          <el-badge :value="alerts.length" :hidden="alerts.length === 0" class="alert-badge">
            <ArtSvgIcon icon="ri:notification-3-line" class="text-lg text-red-500" />
          </el-badge>
          <span class="font-bold">实时告警</span>
        </div>
        <el-button link @click="isExpanded = !isExpanded">
          {{ isExpanded ? '收起' : '展开' }}
          <ArtSvgIcon :icon="isExpanded ? 'ri:arrow-up-s-line' : 'ri:arrow-down-s-line'" />
        </el-button>
      </div>
    </template>

    <el-collapse-transition>
      <div v-show="isExpanded">
        <div v-if="alerts.length === 0" class="py-4 text-center text-g-500 text-sm">
          暂无告警信息
        </div>
        <div v-else class="alert-items">
          <div v-for="alert in alerts" :key="alert.id" class="alert-item" :class="alert.level">
            <div class="flex-cb mb-1">
              <span class="title">{{ alert.title }}</span>
              <span class="time">{{ formatTime(alert.createTime) }}</span>
            </div>
            <p class="message text-sm text-g-600">{{ alert.message }}</p>
          </div>
        </div>
      </div>
    </el-collapse-transition>
  </el-card>
</template>

<script setup lang="ts">
  import { ref } from 'vue'
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import type { Alert } from '@/types/alert'

  defineProps<{
    alerts: Alert[]
  }>()

  const isExpanded = ref(true)

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
    border: 1px solid var(--art-border-color);
    border-radius: 12px;
    box-shadow: 0 2px 8px rgb(15 23 42 / 6%);

    :deep(.el-card__header) {
      padding: 16px;
    }

    :deep(.el-card__body) {
      padding: 0;
    }

    :deep(.el-card__header) {
      border-bottom: 1px solid var(--art-border-color);
    }

    .alert-items {
      max-height: 300px;
      overflow-y: auto;
    }

    .alert-item {
      padding: 12px 16px;
      border-bottom: 1px solid var(--art-border-color);
      transition: background 0.3s;

      &:last-child {
        border-bottom: none;
      }

      &:hover {
        background-color: var(--el-fill-color-light);
      }

      .message {
        margin: 0;
        color: var(--art-gray-600);
      }

      &.high {
        background-color: var(--el-color-danger-light-9);
        border-color: var(--el-color-danger-light-5);

        .title {
          font-weight: bold;
          color: var(--el-color-danger);
        }
      }

      &.critical {
        background-color: var(--el-color-danger-light-9);
        border-color: var(--el-color-danger-light-5);

        .title {
          font-weight: bold;
          color: var(--el-color-danger);
        }
      }

      &.warning {
        background-color: var(--el-color-warning-light-9);
        border-color: var(--el-color-warning-light-5);

        .title {
          font-weight: bold;
          color: var(--el-color-warning);
        }
      }

      .time {
        font-size: 12px;
        color: var(--art-gray-500);
      }
    }
  }

  :global(.dark) .alert-list-card {
    box-shadow: 0 2px 8px rgb(0 0 0 / 20%);

    .alert-item {
      &.high,
      &.critical {
        background-color: color-mix(in oklch, var(--el-color-danger) 12%, transparent);
      }

      &.warning {
        background-color: color-mix(in oklch, var(--el-color-warning) 12%, transparent);
      }
    }
  }
</style>
