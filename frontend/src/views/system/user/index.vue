<template>
  <div class="user-page art-full-height">
    <UserSearch v-model="searchForm" @search="handleSearch" @reset="resetSearchParams" />

    <ElCard class="art-table-card" shadow="never">
      <ArtTableHeader v-model:columns="columnChecks" :loading="loading" @refresh="refreshData">
        <template #left>
          <ElSpace wrap>
            <ElButton v-ripple @click="showDialog('add')">新增用户</ElButton>
          </ElSpace>
        </template>
      </ArtTableHeader>

      <ArtTable
        :loading="loading"
        :data="data"
        :columns="columns"
        :pagination="pagination"
        @selection-change="handleSelectionChange"
        @pagination:size-change="handleSizeChange"
        @pagination:current-change="handleCurrentChange"
      />

      <UserDialog
        ref="userDialogRef"
        v-model:visible="dialogVisible"
        :type="dialogType"
        :user-data="currentUserData"
        @submit="handleDialogSubmit"
      />
    </ElCard>
  </div>
</template>

<script setup lang="ts">
  import { nextTick, ref } from 'vue'
  import { ElMessage, ElMessageBox, ElTag } from 'element-plus'
  import ArtButtonTable from '@/components/core/forms/art-button-table/index.vue'
  import { useTable } from '@/hooks/core/useTable'
  import {
    fetchCreateUser,
    fetchDeleteUser,
    fetchGetUserList,
    fetchUpdateUser
  } from '@/api/system-manage'
  import type { DialogType } from '@/types'
  import UserDialog from './modules/user-dialog.vue'
  import UserSearch from './modules/user-search.vue'

  defineOptions({ name: 'User' })

  type UserListItem = Api.SystemManage.UserListItem

  interface UserDialogExpose {
    formData: {
      username: string
      phone: string
      gender: string
      role: string[]
    }
  }

  const USER_STATUS_CONFIG = {
    '0': { type: 'danger' as const, text: '禁用' },
    '1': { type: 'success' as const, text: '启用' }
  } as const

  const dialogType = ref<DialogType>('add')
  const dialogVisible = ref(false)
  const currentUserData = ref<Partial<UserListItem>>({})
  const userDialogRef = ref<UserDialogExpose | null>(null)
  const selectedRows = ref<UserListItem[]>([])

  const searchForm = ref<{
    keyword?: string
    status: string
  }>({
    keyword: undefined,
    status: '1'
  })

  const getUserStatusConfig = (status: string) => {
    return (
      USER_STATUS_CONFIG[status as keyof typeof USER_STATUS_CONFIG] ?? {
        type: 'info' as const,
        text: '未知'
      }
    )
  }

  const {
    columns,
    columnChecks,
    data,
    loading,
    pagination,
    getData,
    searchParams,
    resetSearchParams,
    handleSizeChange,
    handleCurrentChange,
    refreshData
  } = useTable({
    core: {
      apiFn: fetchGetUserList,
      apiParams: {
        current: 1,
        size: 20,
        ...searchForm.value
      },
      columnsFactory: () => [
        { type: 'selection' },
        { type: 'index', width: 60, label: '序号' },
        {
          prop: 'userName',
          label: '用户名',
          width: 280,
          formatter: (row: UserListItem) => {
            return h('div', { class: 'user flex-c' }, [
              h(
                'div',
                {
                  class:
                    'size-9.5 rounded-md bg-blue-100 flex items-center justify-center text-blue-500'
                },
                row.userName.charAt(0)
              ),
              h('div', { class: 'ml-2' }, [
                h('p', { class: 'user-name' }, row.userName),
                h('p', { class: 'email' }, row.userEmail)
              ])
            ])
          }
        },
        {
          prop: 'userPhone',
          label: '手机号'
        },
        {
          prop: 'status',
          label: '状态',
          formatter: (row: UserListItem) => {
            const statusConfig = getUserStatusConfig(row.status)
            return h(ElTag, { type: statusConfig.type }, () => statusConfig.text)
          }
        },
        {
          prop: 'createTime',
          label: '创建日期',
          sortable: true
        },
        {
          prop: 'operation',
          label: '操作',
          width: 120,
          fixed: 'right',
          formatter: (row: UserListItem) =>
            h('div', [
              h(ArtButtonTable, {
                type: 'edit',
                onClick: () => showDialog('edit', row)
              }),
              h(ArtButtonTable, {
                type: 'delete',
                onClick: () => deleteUser(row)
              })
            ])
        }
      ]
    },
    transform: {
      dataTransformer: (records) => {
        if (!Array.isArray(records)) {
          console.warn('用户列表 records 不是数组:', typeof records)
          return []
        }

        return records.map((item) => ({ ...item }))
      }
    }
  })

  const handleSearch = (params: Record<string, any>) => {
    Object.assign(searchParams, params)
    getData()
  }

  const showDialog = (type: DialogType, row?: UserListItem) => {
    dialogType.value = type
    currentUserData.value = row ?? {}

    nextTick(() => {
      dialogVisible.value = true
    })
  }

  const deleteUser = async (row: UserListItem): Promise<void> => {
    try {
      await ElMessageBox.confirm(`确定要注销用户 ${row.userName} 吗？`, '注销用户', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'error'
      })

      await fetchDeleteUser(row.id)
      ElMessage.success('注销成功')
      refreshData()
    } catch (error) {
      if (error !== 'cancel') {
        console.error('删除失败:', error)
      }
    }
  }

  const handleDialogSubmit = async () => {
    try {
      const formData = userDialogRef.value?.formData
      if (!formData) return

      const payload: Api.SystemManage.UserCreateParams = {
        userName: formData.username,
        userEmail: `${formData.username}@example.com`,
        userPhone: formData.phone,
        userGender: formData.gender,
        userRoles: formData.role,
        password: '123456',
        status: '1'
      }

      if (dialogType.value === 'add') {
        await fetchCreateUser(payload)
        ElMessage.success('添加成功')
      } else if (currentUserData.value.id) {
        const updatePayload: Api.SystemManage.UserUpdateParams = {
          userName: payload.userName,
          userEmail: payload.userEmail,
          userPhone: payload.userPhone,
          userGender: payload.userGender,
          userRoles: payload.userRoles,
          status: payload.status
        }
        await fetchUpdateUser(currentUserData.value.id, updatePayload)
        ElMessage.success('更新成功')
      }

      dialogVisible.value = false
      currentUserData.value = {}
      refreshData()
    } catch (error) {
      console.error('提交失败:', error)
      ElMessage.error('操作失败，请重试')
    }
  }

  const handleSelectionChange = (selection: UserListItem[]) => {
    selectedRows.value = selection
  }
</script>
