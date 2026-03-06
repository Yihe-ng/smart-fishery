<template>
  <div class="pond-list-page art-full-height">
    <el-card class="art-table-card" shadow="never">
      <ArtTableHeader v-model:columns="columnChecks" :loading="loading" @refresh="refreshData">
        <template #left>
          <el-button type="primary" icon="ri:add-line" v-ripple>新增试验池</el-button>
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
  import { getPondList } from '@/api/fish-pond'
  import ArtButtonTable from '@/components/core/forms/art-button-table/index.vue'
  import { ElTag } from 'element-plus'
  import { FishPond } from '@/types'

  defineOptions({ name: 'FishPondList' })

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
      apiFn: getPondList,
      apiParams: {
        current: 1,
        size: 10
      },
      columnsFactory: () => [
        { type: 'index', width: 60, label: '序号' },
        { prop: 'name', label: '池子名称' },
        { prop: 'code', label: '编号' },
        { prop: 'volume', label: '容积 (m³)' },
        { prop: 'fishType', label: '养殖鱼类' },
        { prop: 'fishCount', label: '鱼数量' },
        {
          prop: 'status',
          label: '状态',
          formatter: (row: FishPond) => {
            const statusMap: any = {
              running: { type: 'success', text: '运行中' },
              stopped: { type: 'info', text: '已停止' },
              maintenance: { type: 'warning', text: '维护中' }
            }
            const config = statusMap[row.status] || { type: 'info', text: '未知' }
            return h(ElTag, { type: config.type }, () => config.text)
          }
        },
        { prop: 'createTime', label: '创建日期' },
        {
          prop: 'operation',
          label: '操作',
          width: 120,
          fixed: 'right',
          formatter: (row: FishPond) =>
            h('div', [
              h(ArtButtonTable, {
                type: 'edit',
                onClick: () => console.log('编辑', row)
              }),
              h(ArtButtonTable, {
                type: 'delete',
                onClick: () => console.log('删除', row)
              })
            ])
        }
      ]
    }
  })
</script>
