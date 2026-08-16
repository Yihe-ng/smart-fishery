import request from '@/utils/http'

// 获取用户列表
export function fetchGetUserList(params: Api.SystemManage.UserSearchParams) {
  return request.get<Api.SystemManage.UserList>({
    url: '/api/user/list',
    params
  })
}

// 创建用户
export function fetchCreateUser(data: Api.SystemManage.UserCreateParams) {
  return request.post<Api.SystemManage.UserListItem>({
    url: '/api/user',
    data
  })
}

// 更新用户
export function fetchUpdateUser(id: number, data: Api.SystemManage.UserUpdateParams) {
  return request.put<Api.SystemManage.UserListItem>({
    url: `/api/user/${id}`,
    data
  })
}

// 删除用户
export function fetchDeleteUser(id: number) {
  return request.del<boolean>({
    url: `/api/user/${id}`
  })
}

// 获取角色列表
export function fetchGetRoleList(params: Api.SystemManage.RoleSearchParams) {
  return request.get<Api.SystemManage.RoleList>({
    url: '/api/role/list',
    params
  })
}

// 获取菜单列表
export function fetchGetMenuList() {
  return request.get<MenuTreeNode[]>({
    url: '/api/v3/system/menus/list',
    params: { status: 1 }
  })
}

/** 后端菜单管理接口返回的树形节点（/api/v3/system/menus/list） */
export interface MenuTreeNode {
  id: number
  parentId: number
  menuName: string
  menuCode: string
  menuType: number // 1 目录 2 菜单 3 按钮
  icon: string | null
  path: string | null
  component: string | null
  permission: string | null
  sort: number
  status: number
  createTime: string
  roles: string[] | null
  keepAlive: boolean | null
  isHide: boolean | null
  isHideTab: boolean | null
  link: string | null
  isIframe: boolean | null
  showBadge: boolean | null
  showTextBadge: string | null
  fixedTab: boolean | null
  activePath: string | null
  isFullPage: boolean | null
  children: MenuTreeNode[] | null
}

export interface MenuSaveParams {
  parentId?: number
  menuName?: string
  menuCode?: string
  menuType?: number
  icon?: string | null
  path?: string | null
  component?: string | null
  permission?: string | null
  sort?: number
  status?: number
  roles?: string[] | null
  keepAlive?: boolean | null
  isHide?: boolean | null
  isHideTab?: boolean | null
  link?: string | null
  isIframe?: boolean | null
  showBadge?: boolean | null
  showTextBadge?: string | null
  fixedTab?: boolean | null
  activePath?: string | null
  isFullPage?: boolean | null
}

// 获取菜单树（菜单管理页数据源）
export function fetchGetMenuTree() {
  return request.get<MenuTreeNode[]>({
    url: '/api/v3/system/menus/list'
  })
}

// 创建菜单/按钮
export function fetchCreateMenu(data: MenuSaveParams) {
  return request.post<MenuTreeNode>({
    url: '/api/v3/system/menus',
    data
  })
}

// 更新菜单/按钮
export function fetchUpdateMenu(id: number, data: MenuSaveParams) {
  return request.put<MenuTreeNode>({
    url: `/api/v3/system/menus/${id}`,
    data
  })
}

// 删除菜单/按钮；需要自定义错误提示时传 showErrorMessage: false
export function fetchDeleteMenu(id: number, options?: { showErrorMessage?: boolean }) {
  return request.del<null>({
    url: `/api/v3/system/menus/${id}`,
    showErrorMessage: options?.showErrorMessage ?? true
  })
}
