<template>
  <el-card shadow="hover" class="sensor-card" :class="status" @click="emit('click', device)">
    <div class="flex-cb">
      <div class="flex-c gap-2">
        <div class="status-dot"></div>
        <span class="name">{{ device.name }}</span>
      </div>
      <el-tag :type="statusTagType" size="small">{{ statusText }}</el-tag>
    </div>
    <div class="mt-2 text-sm text-[var(--el-text-color-secondary)] flex-cb">
      <span>{{ device.location }}</span>
      <span class="font-bold text-[var(--el-text-color-primary)]"
        >{{ device.lastData }}{{ device.unit }}</span
      >
    </div>
  </el-card>
</template>

<script setup lang="ts">
  import { computed } from 'vue'
  import type { SensorDevice } from '@/types/device'

  const props = defineProps<{
    device: SensorDevice
  }>()

  const emit = defineEmits<{
    click: [device: SensorDevice]
  }>()

  const status = computed(() => props.device.status)

  const statusTagType = computed(() => {
    const map: any = { online: 'success', offline: 'info', error: 'danger' }
    return map[props.device.status] || 'info'
  })

  const statusText = computed(() => {
    const map: any = { online: '在线', offline: '离线', error: '故障' }
    return map[props.device.status] || '未知'
  })
</script>

<style scoped lang="scss">
  .sensor-card {
    margin-bottom: 8px;
    cursor: pointer;
    border-left: 4px solid transparent;

    &.online {
      border-left-color: var(--el-color-success);

      .status-dot {
        background-color: var(--el-color-success);
      }
    }

    &.offline {
      border-left-color: var(--el-color-info);

      .status-dot {
        background-color: var(--el-color-info);
      }
    }

    &.error {
      border-left-color: var(--el-color-danger);

      .status-dot {
        background-color: var(--el-color-danger);
      }
    }

    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
    }

    .name {
      font-size: 14px;
      font-weight: 500;
    }
  }
</style>
