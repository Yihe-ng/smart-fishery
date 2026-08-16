<!-- 菜单管理页面 -->
<template>
  <div class="menu-page art-full-height">
    <!-- 搜索栏 -->
    <ArtSearchBar
      v-model="formFilters"
      :items="formItems"
      :showExpand="false"
      @reset="handleReset"
      @search="handleSearch"
    />

    <ElCard class="art-table-card" shadow="never">
      <!-- 表格头部 -->
      <ArtTableHeader
        :showZebra="false"
        :loading="loading"
        v-model:columns="columnChecks"
        @refresh="handleRefresh"
      >
        <template #left>
          <ElButton v-auth="'add'" @click="handleAddMenu" v-ripple> 添加菜单 </ElButton>
          <ElButton @click="toggleExpand" v-ripple>
            {{ isExpanded ? '收起' : '展开' }}
          </ElButton>
        </template>
      </ArtTableHeader>

      <ArtTable
        ref="tableRef"
        rowKey="path"
        :loading="loading"
        :columns="columns"
        :data="filteredTableData"
        :stripe="false"
        :tree-props="{ children: 'children', hasChildren: 'hasChildren' }"
        :default-expand-all="false"
      />

      <!-- 菜单弹窗 -->
      <MenuDialog
        v-model:visible="dialogVisible"
        :type="dialogType"
        :editData="editData"
        :lockType="lockMenuType"
        @submit="handleSubmit"
      />
    </ElCard>
  </div>
</template>

<script setup lang="ts">
  import { formatMenuTitle } from '@/utils/router'
  import ArtButtonTable from '@/components/core/forms/art-button-table/index.vue'
  import { useTableColumns } from '@/hooks/core/useTableColumns'
  import type { AppRouteRecord } from '@/types/router'
  import MenuDialog from './modules/menu-dialog.vue'
  import {
    fetchCreateMenu,
    fetchDeleteMenu,
    fetchGetMenuTree,
    fetchUpdateMenu,
    type MenuSaveParams,
    type MenuTreeNode
  } from '@/api/system-manage'
  import { ElMessage, ElTag, ElMessageBox } from 'element-plus'

  defineOptions({ name: 'Menus' })

  // 状态管理
  const loading = ref(false)
  const isExpanded = ref(false)
  const tableRef = ref()

  // 弹窗相关
  const dialogVisible = ref(false)
  const dialogType = ref<'menu' | 'button'>('menu')
  const editData = ref<AppRouteRecord | any>(null)
  const lockMenuType = ref(false)

  // 搜索相关
  const initialSearchState = {
    name: '',
    route: ''
  }

  const formFilters = reactive({ ...initialSearchState })
  const appliedFilters = reactive({ ...initialSearchState })

  const formItems = computed(() => [
    {
      label: '菜单名称',
      key: 'name',
      type: 'input',
      props: { clearable: true }
    },
    {
      label: '路由地址',
      key: 'route',
      type: 'input',
      props: { clearable: true }
    }
  ])

  onMounted(() => {
    getMenuList()
  })

  /** 表格行：后端菜单节点映射为路由记录，并附带编辑时间/状态列所需字段 */
  interface MenuRowRecord extends AppRouteRecord {
    createTime: string
    status: number
  }

  /**
   * 把后端菜单树映射为页面需要的路由记录树：
   * 按钮节点（menuType=3）转为父菜单 meta.authList 的权限标识；
   * 节点 id 保留在行对象上，供编辑/删除接口使用。
   */
  const toMenuRowRecords = (nodes: MenuTreeNode[]): MenuRowRecord[] => {
    return nodes.map((node) => {
      const buttonChildren = (node.children ?? []).filter((child) => child.menuType === 3)
      const menuChildren = (node.children ?? []).filter((child) => child.menuType !== 3)
      const authList = buttonChildren.map((button) => ({
        id: button.id,
        parentId: node.id,
        parentCode: node.menuCode,
        title: button.menuName,
        authMark: button.permission ?? ''
      }))

      return {
        id: node.id,
        path: node.path ?? '',
        name: node.menuCode,
        component: node.component ?? '',
        createTime: node.createTime,
        status: node.status,
        children: toMenuRowRecords(menuChildren),
        meta: {
          title: node.menuName,
          icon: node.icon ?? undefined,
          sort: node.sort,
          isEnable: node.status !== 0,
          roles: node.roles ?? undefined,
          keepAlive: node.keepAlive ?? undefined,
          isHide: node.isHide ?? undefined,
          isHideTab: node.isHideTab ?? undefined,
          link: node.link ?? undefined,
          isIframe: node.isIframe ?? undefined,
          showBadge: node.showBadge ?? undefined,
          showTextBadge: node.showTextBadge ?? undefined,
          fixedTab: node.fixedTab ?? undefined,
          activePath: node.activePath ?? undefined,
          isFullPage: node.isFullPage ?? undefined,
          authList: authList.length ? authList : undefined
        }
      }
    })
  }

  /**
   * 获取菜单列表数据
   */
  const getMenuList = async (): Promise<void> => {
    loading.value = true

    try {
      const tree = await fetchGetMenuTree()
      tableData.value = toMenuRowRecords(tree)
    } catch (error) {
      throw error instanceof Error ? error : new Error('获取菜单失败')
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取菜单类型标签颜色
   * @param row 菜单行数据
   * @returns 标签颜色类型
   */
  const getMenuTypeTag = (
    row: AppRouteRecord
  ): 'primary' | 'success' | 'warning' | 'info' | 'danger' => {
    if (row.meta?.isAuthButton) return 'danger'
    if (row.children?.length) return 'info'
    if (row.meta?.link && row.meta?.isIframe) return 'success'
    if (row.path) return 'primary'
    if (row.meta?.link) return 'warning'
    return 'info'
  }

  /**
   * 获取菜单类型文本
   * @param row 菜单行数据
   * @returns 菜单类型文本
   */
  const getMenuTypeText = (row: AppRouteRecord): string => {
    if (row.meta?.isAuthButton) return '按钮'
    if (row.children?.length) return '目录'
    if (row.meta?.link && row.meta?.isIframe) return '内嵌'
    if (row.path) return '菜单'
    if (row.meta?.link) return '外链'
    return '未知'
  }

  // 表格列配置
  const { columnChecks, columns } = useTableColumns(() => [
    {
      prop: 'meta.title',
      label: '菜单名称',
      minWidth: 120,
      formatter: (row: AppRouteRecord) => formatMenuTitle(row.meta?.title)
    },
    {
      prop: 'type',
      label: '菜单类型',
      formatter: (row: AppRouteRecord) => {
        return h(ElTag, { type: getMenuTypeTag(row) }, () => getMenuTypeText(row))
      }
    },
    {
      prop: 'path',
      label: '路由',
      formatter: (row: AppRouteRecord) => {
        if (row.meta?.isAuthButton) return ''
        return row.meta?.link || row.path || ''
      }
    },
    {
      prop: 'meta.authList',
      label: '权限标识',
      formatter: (row: AppRouteRecord) => {
        if (row.meta?.isAuthButton) {
          return row.meta?.authMark || ''
        }
        if (!row.meta?.authList?.length) return ''
        return `${row.meta.authList.length} 个权限标识`
      }
    },
    {
      prop: 'createTime',
      label: '编辑时间',
      formatter: (row: AppRouteRecord) => (row as MenuRowRecord).createTime || '-'
    },
    {
      prop: 'status',
      label: '状态',
      formatter: (row: AppRouteRecord) => {
        // isHide（侧边栏隐藏）与 status（启用/停用）是两个字段，隐藏态优先展示
        if (row.meta?.isHide) {
          return h(ElTag, { type: 'info' }, () => '隐藏')
        }
        const disabled = (row as MenuRowRecord).status === 0
        return h(ElTag, { type: disabled ? 'danger' : 'success' }, () =>
          disabled ? '停用' : '启用'
        )
      }
    },
    {
      prop: 'operation',
      label: '操作',
      width: 180,
      align: 'right',
      formatter: (row: AppRouteRecord) => {
        const buttonStyle = { style: 'text-align: right' }

        if (row.meta?.isAuthButton) {
          return h('div', buttonStyle, [
            h(ArtButtonTable, {
              type: 'edit',
              onClick: () => handleEditAuth(row)
            }),
            h(ArtButtonTable, {
              type: 'delete',
              onClick: () => handleDeleteAuth(row)
            })
          ])
        }

        return h('div', buttonStyle, [
          h(ArtButtonTable, {
            type: 'add',
            onClick: () => handleAddAuth(row),
            title: '新增权限'
          }),
          h(ArtButtonTable, {
            type: 'edit',
            onClick: () => handleEditMenu(row)
          }),
          h(ArtButtonTable, {
            type: 'delete',
            onClick: () => handleDeleteMenu(row)
          })
        ])
      }
    }
  ])

  // 数据相关
  const tableData = ref<AppRouteRecord[]>([])

  /**
   * 重置搜索条件
   */
  const handleReset = (): void => {
    Object.assign(formFilters, { ...initialSearchState })
    Object.assign(appliedFilters, { ...initialSearchState })
    getMenuList()
  }

  /**
   * 执行搜索
   */
  const handleSearch = (): void => {
    Object.assign(appliedFilters, { ...formFilters })
    getMenuList()
  }

  /**
   * 刷新菜单列表
   */
  const handleRefresh = (): void => {
    getMenuList()
  }

  /**
   * 深度克隆对象
   * @param obj 要克隆的对象
   * @returns 克隆后的对象
   */
  const deepClone = <T,>(obj: T): T => {
    if (obj === null || typeof obj !== 'object') return obj
    if (obj instanceof Date) return new Date(obj) as T
    if (Array.isArray(obj)) return obj.map((item) => deepClone(item)) as T

    const cloned = {} as T
    for (const key in obj) {
      if (Object.prototype.hasOwnProperty.call(obj, key)) {
        cloned[key] = deepClone(obj[key])
      }
    }
    return cloned
  }

  /**
   * 将权限列表转换为子节点
   * @param items 菜单项数组
   * @returns 转换后的菜单项数组
   */
  const convertAuthListToChildren = (items: AppRouteRecord[]): AppRouteRecord[] => {
    return items.map((item) => {
      const clonedItem = deepClone(item)

      if (clonedItem.children?.length) {
        clonedItem.children = convertAuthListToChildren(clonedItem.children)
      }

      if (item.meta?.authList?.length) {
        const authChildren: AppRouteRecord[] = item.meta.authList.map(
          (auth: {
            id?: number
            parentId?: number
            parentCode?: string
            title: string
            authMark: string
          }) => ({
            id: auth.id,
            path: `${item.path}_auth_${auth.authMark}`,
            name: `${String(item.name)}_auth_${auth.authMark}`,
            meta: {
              title: auth.title,
              authMark: auth.authMark,
              isAuthButton: true,
              parentPath: item.path,
              parentId: auth.parentId,
              parentCode: auth.parentCode
            }
          })
        )

        clonedItem.children = clonedItem.children?.length
          ? [...clonedItem.children, ...authChildren]
          : authChildren
      }

      return clonedItem
    })
  }

  /**
   * 搜索菜单
   * @param items 菜单项数组
   * @returns 搜索结果数组
   */
  const searchMenu = (items: AppRouteRecord[]): AppRouteRecord[] => {
    const results: AppRouteRecord[] = []

    for (const item of items) {
      const searchName = appliedFilters.name?.toLowerCase().trim() || ''
      const searchRoute = appliedFilters.route?.toLowerCase().trim() || ''
      const menuTitle = formatMenuTitle(item.meta?.title || '').toLowerCase()
      const menuPath = (item.path || '').toLowerCase()
      const nameMatch = !searchName || menuTitle.includes(searchName)
      const routeMatch = !searchRoute || menuPath.includes(searchRoute)

      if (item.children?.length) {
        const matchedChildren = searchMenu(item.children)
        if (matchedChildren.length > 0) {
          const clonedItem = deepClone(item)
          clonedItem.children = matchedChildren
          results.push(clonedItem)
          continue
        }
      }

      if (nameMatch && routeMatch) {
        results.push(deepClone(item))
      }
    }

    return results
  }

  // 过滤后的表格数据
  const filteredTableData = computed(() => {
    const searchedData = searchMenu(tableData.value)
    return convertAuthListToChildren(searchedData)
  })

  /**
   * 添加菜单
   */
  const handleAddMenu = (): void => {
    dialogType.value = 'menu'
    editData.value = null
    lockMenuType.value = true
    dialogVisible.value = true
  }

  /** 新增按钮权限的挂载信息：父菜单 id 与路由 name（用于生成按钮 menuCode） */
  let buttonParentId = 0
  let buttonParentCode = ''

  /**
   * 添加权限按钮
   * @param row 权限挂载的父菜单行
   */
  const handleAddAuth = (row: AppRouteRecord): void => {
    dialogType.value = 'menu'
    editData.value = null
    lockMenuType.value = false
    buttonParentId = Number(row.id ?? 0)
    buttonParentCode = String(row.name ?? '')
    dialogVisible.value = true
  }

  /**
   * 编辑菜单
   * @param row 菜单行数据
   */
  const handleEditMenu = (row: AppRouteRecord): void => {
    dialogType.value = 'menu'
    editData.value = row
    lockMenuType.value = true
    dialogVisible.value = true
  }

  /**
   * 编辑权限按钮
   * @param row 权限行数据
   */
  const handleEditAuth = (row: AppRouteRecord): void => {
    dialogType.value = 'button'
    editData.value = {
      id: row.id,
      title: row.meta?.title,
      authMark: row.meta?.authMark
    }
    buttonParentId = Number((row.meta as { parentId?: number }).parentId ?? 0)
    buttonParentCode = String((row.meta as { parentCode?: string }).parentCode ?? '')
    lockMenuType.value = false
    dialogVisible.value = true
  }

  /**
   * 菜单表单数据类型
   */
  interface MenuFormData {
    id: number
    name: string
    path: string
    component?: string
    icon?: string
    roles?: string[]
    sort?: number
    isEnable?: boolean
    keepAlive?: boolean
    isHide?: boolean
    isHideTab?: boolean
    label?: string
    authName?: string
    authLabel?: string
    authSort?: number
    menuType?: 'menu' | 'button'
    [key: string]: any
  }

  /** 从 http 错误中提取后端 detail 文案（如"该菜单下有子菜单，无法删除"） */
  const getMenuErrorText = (error: unknown, fallback: string): string => {
    const detail = (error as { data?: { detail?: string } })?.data?.detail
    return detail || fallback
  }

  /**
   * 提交表单数据：新增/编辑 菜单或按钮权限
   * @param formData 表单数据
   */
  const handleSubmit = async (formData: MenuFormData): Promise<void> => {
    const editing = formData.id > 0

    try {
      if (formData.menuType === 'button') {
        const payload: MenuSaveParams = {
          parentId: buttonParentId,
          menuName: formData.authName ?? '',
          menuCode: `${buttonParentCode || 'Menu'}_${formData.authLabel ?? ''}`,
          menuType: 3,
          permission: formData.authLabel ?? '',
          sort: formData.authSort ?? 1
        }
        if (editing) {
          await fetchUpdateMenu(formData.id, payload)
        } else {
          await fetchCreateMenu(payload)
        }
      } else {
        const payload: MenuSaveParams = {
          menuName: formData.name,
          menuCode: formData.label || formData.name,
          menuType: 2,
          icon: formData.icon || null,
          path: formData.path || null,
          component: formData.component || null,
          sort: formData.sort ?? 1,
          status: formData.isEnable === false ? 0 : 1,
          roles: formData.roles?.length ? formData.roles : null,
          keepAlive: formData.keepAlive ?? null,
          isHide: formData.isHide ?? null,
          isHideTab: formData.isHideTab ?? null,
          link: formData.link || null,
          isIframe: formData.isIframe ?? null,
          showBadge: formData.showBadge ?? null,
          showTextBadge: formData.showTextBadge || null,
          fixedTab: formData.fixedTab ?? null,
          activePath: formData.activePath || null,
          isFullPage: formData.isFullPage ?? null
        }
        if (editing) {
          await fetchUpdateMenu(formData.id, payload)
        } else {
          await fetchCreateMenu({ parentId: 0, ...payload })
        }
      }

      ElMessage.success(`${editing ? '编辑' : '新增'}成功`)
      getMenuList()
    } catch (error) {
      console.warn('[Menus] 保存菜单失败:', error)
    }
  }

  /**
   * 删除菜单
   * @param row 菜单行数据
   */
  const handleDeleteMenu = async (row: AppRouteRecord): Promise<void> => {
    try {
      await ElMessageBox.confirm('确定要删除该菜单吗？删除后无法恢复', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      })
    } catch {
      return
    }

    try {
      await fetchDeleteMenu(Number(row.id), { showErrorMessage: false })
      ElMessage.success('删除成功')
      getMenuList()
    } catch (error) {
      ElMessage.error(getMenuErrorText(error, '删除失败'))
    }
  }

  /**
   * 删除权限按钮
   * @param row 权限行数据
   */
  const handleDeleteAuth = async (row: AppRouteRecord): Promise<void> => {
    try {
      await ElMessageBox.confirm('确定要删除该权限吗？删除后无法恢复', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      })
    } catch {
      return
    }

    try {
      await fetchDeleteMenu(Number(row.id), { showErrorMessage: false })
      ElMessage.success('删除成功')
      getMenuList()
    } catch (error) {
      ElMessage.error(getMenuErrorText(error, '删除失败'))
    }
  }

  /**
   * 切换展开/收起所有菜单
   */
  const toggleExpand = (): void => {
    isExpanded.value = !isExpanded.value
    nextTick(() => {
      if (tableRef.value?.elTableRef && filteredTableData.value) {
        const processRows = (rows: AppRouteRecord[]) => {
          rows.forEach((row) => {
            if (row.children?.length) {
              tableRef.value.elTableRef.toggleRowExpansion(row, isExpanded.value)
              processRows(row.children)
            }
          })
        }
        processRows(filteredTableData.value)
      }
    })
  }
</script>
