import request from '@/utils/http'
import { AppRouteRecord } from '@/types/router'

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
  return request.delete<boolean>({
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
  return request.get<AppRouteRecord[]>({
    url: '/api/v3/system/menus/simple'
  })
}
