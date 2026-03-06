<template>
  <el-card class="detect-stats-table">
    <template #header>
      <div class="card-header">
        <ArtSvgIcon icon="ri:bar-chart-fill" />
        <span>病害统计</span>
      </div>
    </template>
    <el-table :data="tableData" style="width: 100%">
      <el-table-column prop="type" label="病害类型" />
      <el-table-column prop="count" label="数量" align="center">
        <template #default="{ row }">
          <el-tag :type="row.count > 0 ? 'danger' : 'info'">
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
  import type { DiseaseStats } from '@/types/fish-disease'

  const props = defineProps<{
    stats: DiseaseStats
  }>()

  const tableData = computed(() => [
    { type: '烂鳃', count: props.stats['烂鳃'] },
    { type: '赤皮', count: props.stats['赤皮'] },
    { type: '肠炎', count: props.stats['肠炎'] }
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
