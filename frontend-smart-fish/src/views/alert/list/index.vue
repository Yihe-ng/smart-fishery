<template>
  <div class="alert-list-page art-full-height">
    <el-card class="art-table-card" shadow="never">
      <ArtTableHeader v-model:columns="columnChecks" :loading="loading" @refresh="refreshData">
        <template #left>
          <el-space>
            <el-button type="danger" plain icon="ri:check-double-line">全部标为已读</el-button>
          </el-space>
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
  import { getAlertList } from '@/api/alert'
  import ArtButtonTable from '@/components/core/forms/art-button-table/index.vue'
  import { ElTag } from 'element-plus'
  import { Alert } from '@/types'

  defineOptions({ name: 'AlertList' })

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
      apiFn: getAlertList,
      apiParams: {
        current: 1,
        size: 10
      },
      columnsFactory: () => [
        { type: 'index', width: 60, label: '序号' },
        {
          prop: 'level',
          label: '级别',
          width: 100,
          formatter: (row: Alert) => {
            const levelMap: any = {
              critical: { type: 'danger', text: '紧急' },
              warning: { type: 'warning', text: '警告' },
              info: { type: 'info', text: '提示' }
            }
            const config = levelMap[row.level] || { type: 'info', text: '普通' }
            return h(ElTag, { type: config.type, effect: 'dark' }, () => config.text)
          }
        },
        { prop: 'type', label: '类型' },
        { prop: 'message', label: '告警内容', minWidth: 250 },
        { prop: 'createTime', label: '发生时间', width: 180 },
        {
          prop: 'status',
          label: '状态',
          width: 100,
          formatter: (row: Alert) => {
            return h(ElTag, { type: row.status === 'resolved' ? 'success' : 'danger' }, () =>
              row.status === 'resolved' ? '已处理' : '待处理'
            )
          }
        },
        {
          prop: 'operation',
          label: '操作',
          width: 100,
          fixed: 'right',
          formatter: (row: Alert) =>
            h('div', [
              h(ArtButtonTable, {
                type: 'edit',
                text: '处理',
                onClick: () => console.log('处理', row)
              })
            ])
        }
      ]
    }
  })
</script>
