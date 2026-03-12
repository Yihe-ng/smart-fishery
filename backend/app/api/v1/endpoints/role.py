from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class RoleListItem(BaseModel):
    """角色列表项"""
    id: int
    roleName: str
    roleCode: str
    description: Optional[str] = None
    status: int
    createTime: str


class RoleListResponse(BaseModel):
    """角色列表响应"""
    code: int
    msg: str
    data: dict


class RoleCreateRequest(BaseModel):
    """创建角色请求"""
    roleName: str
    roleCode: str
    description: Optional[str] = None
    status: int = 1
    menuIds: List[int] = []


class RoleUpdateRequest(BaseModel):
    """更新角色请求"""
    roleName: Optional[str] = None
    roleCode: Optional[str] = None
    description: Optional[str] = None
    status: Optional[int] = None
    menuIds: Optional[List[int]] = None


# 模拟角色数据
mock_roles = [
    {
        "id": 1,
        "roleName": "超级管理员",
        "roleCode": "super_admin",
        "description": "系统超级管理员，拥有所有权限",
        "status": 1,
        "createTime": "2024-01-01 00:00:00"
    },
    {
        "id": 2,
        "roleName": "普通用户",
        "roleCode": "user",
        "description": "普通用户，拥有基本权限",
        "status": 1,
        "createTime": "2024-01-02 00:00:00"
    },
    {
        "id": 3,
        "roleName": "访客",
        "roleCode": "guest",
        "description": "访客用户，仅拥有查看权限",
        "status": 1,
        "createTime": "2024-01-03 00:00:00"
    }
]


@router.get("/list", response_model=RoleListResponse)
async def get_role_list(
    current: int = Query(1, description="当前页码"),
    size: int = Query(20, description="每页大小"),
    status: Optional[int] = Query(None, description="状态筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索")
):
    """获取角色列表"""
    # 筛选数据
    filtered_roles = mock_roles.copy()
    
    if status is not None:
        filtered_roles = [r for r in filtered_roles if r["status"] == status]
    
    if keyword:
        filtered_roles = [
            r for r in filtered_roles 
            if keyword.lower() in r["roleName"].lower() 
            or keyword.lower() in r["roleCode"].lower()
        ]
    
    # 分页
    total = len(filtered_roles)
    start = (current - 1) * size
    end = start + size
    page_data = filtered_roles[start:end]
    
    return RoleListResponse(
        code=200,
        msg="success",
        data={
            "list": page_data,
            "total": total,
            "current": current,
            "size": size
        }
    )


@router.get("/{role_id}")
async def get_role(role_id: int):
    """获取角色详情"""
    role = next((r for r in mock_roles if r["id"] == role_id), None)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    return {
        "code": 200,
        "msg": "success",
        "data": role
    }


@router.post("")
async def create_role(request: RoleCreateRequest):
    """创建角色"""
    new_role = {
        "id": len(mock_roles) + 1,
        "roleName": request.roleName,
        "roleCode": request.roleCode,
        "description": request.description,
        "status": request.status,
        "createTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    mock_roles.append(new_role)
    
    return {
        "code": 200,
        "msg": "创建成功",
        "data": new_role
    }


@router.put("/{role_id}")
async def update_role(role_id: int, request: RoleUpdateRequest):
    """更新角色"""
    role = next((r for r in mock_roles if r["id"] == role_id), None)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    if request.roleName:
        role["roleName"] = request.roleName
    if request.roleCode:
        role["roleCode"] = request.roleCode
    if request.description:
        role["description"] = request.description
    if request.status is not None:
        role["status"] = request.status
    
    return {
        "code": 200,
        "msg": "更新成功",
        "data": role
    }


@router.delete("/{role_id}")
async def delete_role(role_id: int):
    """删除角色"""
    global mock_roles
    role = next((r for r in mock_roles if r["id"] == role_id), None)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    mock_roles = [r for r in mock_roles if r["id"] != role_id]
    
    return {
        "code": 200,
        "msg": "删除成功",
        "data": None
    }


@router.get("/{role_id}/menus")
async def get_role_menus(role_id: int):
    """获取角色的菜单权限"""
    role = next((r for r in mock_roles if r["id"] == role_id), None)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    # 返回模拟的菜单ID列表
    return {
        "code": 200,
        "msg": "success",
        "data": [1, 2, 3, 4, 5]  # 模拟菜单ID列表
    }


@router.put("/{role_id}/menus")
async def update_role_menus(role_id: int, menu_ids: List[int]):
    """更新角色的菜单权限"""
    role = next((r for r in mock_roles if r["id"] == role_id), None)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    return {
        "code": 200,
        "msg": "更新成功",
        "data": menu_ids
    }
