<template>
  <div class="data-management-page page-container">
    <el-row :gutter="20" class="mb-5">
      <el-col :xs="24" :sm="8">
        <el-card shadow="hover">
          <template #header>
            <span class="font-bold">存储后端</span>
          </template>
          <div class="flex-cb">
            <span class="text-sm">{{ backendLabel }}</span>
            <el-tag :type="isLocal ? 'primary' : 'warning'" size="small">
              {{ status?.backend || '—' }}
            </el-tag>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card shadow="hover">
          <template #header>
            <span class="font-bold">上次清理</span>
          </template>
          <template v-if="status?.lastCleanup">
            <div class="text-sm">{{ formatTime(status.lastCleanup.time) }}</div>
            <div class="mt-1 text-xs text-[var(--el-text-color-secondary)]">
              清理对象：{{ status.lastCleanup.deleted }} 个
            </div>
          </template>
          <el-tag v-else type="info" size="small">从未执行</el-tag>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card shadow="hover">
          <template #header>
            <span class="font-bold">当前数据总量</span>
          </template>
          <div class="text-xl font-bold">{{ formatBytes(totalBytes) }}</div>
          <div class="mt-1 text-xs text-[var(--el-text-color-secondary)]">
            各保留前缀对象数合计
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never">
      <template #header>
        <span class="font-bold">保留策略</span>
      </template>
      <div class="text-sm text-[var(--el-text-color-secondary)]">
        每月 1 日凌晨 3:00 由调度器自动清理超期对象
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
  import { computed, onMounted, ref } from 'vue'
  import { fetchStorageStatus, type StorageStatus } from '@/api/storage'

  defineOptions({ name: 'DataManagement' })

  const status = ref<StorageStatus | null>(null)

  const backendLabel = computed(() => {
    const backend = status.value?.backend
    if (backend === 'object') return '对象存储（S3 / MinIO）'
    if (backend === 'local') return '本地文件系统'
    return backend || '—'
  })

  const isLocal = computed(() => status.value?.backend === 'local')

  const totalBytes = computed(() =>
    (status.value?.rules ?? []).reduce((sum, rule) => sum + rule.totalBytes, 0)
  )

  const formatBytes = (n: number) => {
    if (!n || n <= 0) return '0 B'
    const units = ['B', 'KB', 'MB', 'GB', 'TB']
    let index = 0
    let value = n
    while (value >= 1024 && index < units.length - 1) {
      value /= 1024
      index += 1
    }
    const digits = index === 0 || value >= 100 ? 0 : 1
    return `${value.toFixed(digits)} ${units[index]}`
  }

  const formatTime = (iso: string) => {
    const date = new Date(iso)
    if (Number.isNaN(date.getTime())) return iso
    const pad = (x: number) => String(x).padStart(2, '0')
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ` +
      `${pad(date.getHours())}:${pad(date.getMinutes())}`
  }

  const loadData = async () => {
    status.value = await fetchStorageStatus()
  }

  onMounted(loadData)
</script>

<style scoped lang="scss">
  .data-management-page {
    padding: 20px;
  }
</style>
