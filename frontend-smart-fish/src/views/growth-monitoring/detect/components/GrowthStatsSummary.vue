<template>
  <el-card class="detect-stats-table">
    <template #header>
      <div class="card-header">
        <ArtSvgIcon icon="ri:bar-chart-fill" />
        <span>生长状态分布</span>
      </div>
    </template>
    <el-table :data="tableData" style="width: 100%">
      <el-table-column prop="type" label="生长状态" />
      <el-table-column prop="count" label="数量" align="center">
        <template #default="{ row }">
          <el-tag :type="row.tagType">
            {{ row.count }}
          </el-tag>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup lang="ts">
  import { computed } from 'vue'
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import type { GrowthStats } from '@/types/growth-monitoring'

  const props = defineProps<{
    stats: GrowthStats
  }>()

  const tableData = computed(() => [
    { type: '偏小', count: props.stats.small, tagType: 'warning' },
    { type: '正常', count: props.stats.normal, tagType: 'success' },
    { type: '偏大', count: props.stats.large, tagType: 'primary' }
  ])
</script>

<style scoped lang="scss">
  .detect-stats-table {
    .card-header {
      display: flex;
      gap: 8px;
      align-items: center;
      font-weight: bold;
    }
  }
</style>
