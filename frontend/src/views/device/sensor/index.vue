<template>
  <div class="sensor-manage-page art-full-height">
    <el-card class="art-table-card" shadow="never">
      <ArtTableHeader v-model:columns="columnChecks" :loading="loading" @refresh="refreshData">
        <template #left>
          <el-button type="primary" icon="ri:add-line">新增传感器</el-button>
        </template>
      </ArtTableHeader>

      <ArtTable
        :loading="loading"
        :data="data"
        :columns="columns"
        :pagination="pagination"
        @pagination:size-change="handleSizeChange"
        @pagination:current-change="handleCurrentChange"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
  import { useTable } from '@/hooks/core/useTable'

  const {
    columns,
    columnChecks,
    data,
    loading,
    pagination,
    handleSizeChange,
    handleCurrentChange,
    refreshData
  } = useTable({
    core: {
      apiFn: () => Promise.resolve({ list: [], total: 0 }),
      apiParams: { current: 1, size: 10 },
      columnsFactory: () => [
        { type: 'index', width: 60, label: '序号' },
        { prop: 'name', label: '设备名称' },
        { prop: 'code', label: '编号' },
        { prop: 'type', label: '类型' },
        { prop: 'pondId', label: '所属池子' },
        { prop: 'status', label: '状态' },
        { prop: 'lastOnlineTime', label: '最后在线' },
        { prop: 'operation', label: '操作', width: 120, fixed: 'right' }
      ]
    }
  })
</script>
