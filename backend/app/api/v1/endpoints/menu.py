from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class MenuItem(BaseModel):
    """菜单项"""
    id: int
    parentId: int
    menuName: str
    menuCode: str
    menuType: int  # 1: 目录, 2: 菜单, 3: 按钮
    icon: Optional[str] = None
    path: Optional[str] = None
    component: Optional[str] = None
    permission: Optional[str] = None
    sort: int = 0
    status: int = 1
    createTime: str
    children: Optional[List['MenuItem']] = None


class MenuSimpleItem(BaseModel):
    """简化菜单项（用于选择）"""
    id: int
    parentId: int
    menuName: str
    menuType: int


class MenuListResponse(BaseModel):
    """菜单列表响应"""
    code: int
    msg: str
    data: List[MenuItem]


class MenuSimpleResponse(BaseModel):
    """简化菜单列表响应"""
    code: int
    msg: str
    data: List[MenuSimpleItem]


class MenuCreateRequest(BaseModel):
    """创建菜单请求"""
    parentId: int = 0
    menuName: str
    menuCode: str
    menuType: int
    icon: Optional[str] = None
    path: Optional[str] = None
    component: Optional[str] = None
    permission: Optional[str] = None
    sort: int = 0
    status: int = 1


class MenuUpdateRequest(BaseModel):
    """更新菜单请求"""
    parentId: Optional[int] = None
    menuName: Optional[str] = None
    menuCode: Optional[str] = None
    menuType: Optional[int] = None
    icon: Optional[str] = None
    path: Optional[str] = None
    component: Optional[str] = None
    permission: Optional[str] = None
    sort: Optional[int] = None
    status: Optional[int] = None


# 模拟菜单数据
mock_menus = [
    {
        "id": 1,
        "parentId": 0,
        "menuName": "系统管理",
        "menuCode": "system",
        "menuType": 1,
        "icon": "SettingOutlined",
        "path": "/system",
        "component": None,
        "permission": None,
        "sort": 1,
        "status": 1,
        "createTime": "2024-01-01 00:00:00"
    },
    {
        "id": 2,
        "parentId": 1,
        "menuName": "用户管理",
        "menuCode": "user",
        "menuType": 2,
        "icon": "UserOutlined",
        "path": "/system/user",
        "component": "system/user/index",
        "permission": "system:user:list",
        "sort": 1,
        "status": 1,
        "createTime": "2024-01-01 00:00:00"
    },
    {
        "id": 3,
        "parentId": 1,
        "menuName": "角色管理",
        "menuCode": "role",
        "menuType": 2,
        "icon": "TeamOutlined",
        "path": "/system/role",
        "component": "system/role/index",
        "permission": "system:role:list",
        "sort": 2,
        "status": 1,
        "createTime": "2024-01-01 00:00:00"
    },
    {
        "id": 4,
        "parentId": 1,
        "menuName": "菜单管理",
        "menuCode": "menu",
        "menuType": 2,
        "icon": "MenuOutlined",
        "path": "/system/menu",
        "component": "system/menu/index",
        "permission": "system:menu:list",
        "sort": 3,
        "status": 1,
        "createTime": "2024-01-01 00:00:00"
    },
    {
        "id": 5,
        "parentId": 0,
        "menuName": "水质监测",
        "menuCode": "water",
        "menuType": 1,
        "icon": "DashboardOutlined",
        "path": "/water",
        "component": None,
        "permission": None,
        "sort": 2,
        "status": 1,
        "createTime": "2024-01-02 00:00:00"
    },
    {
        "id": 6,
        "parentId": 5,
        "menuName": "实时监测",
        "menuCode": "water-monitor",
        "menuType": 2,
        "icon": "LineChartOutlined",
        "path": "/water/monitor",
        "component": "water/monitor/index",
        "permission": "water:monitor:list",
        "sort": 1,
        "status": 1,
        "createTime": "2024-01-02 00:00:00"
    }
]


def build_menu_tree(menus: List[dict], parent_id: int = 0) -> List[dict]:
    """构建菜单树"""
    tree = []
    for menu in menus:
        if menu["parentId"] == parent_id:
            children = build_menu_tree(menus, menu["id"])
            if children:
                menu["children"] = children
            tree.append(menu)
    return tree


@router.get("/list", response_model=MenuListResponse)
async def get_menu_list(
    status: Optional[int] = Query(None, description="状态筛选")
):
    """获取菜单列表（树形结构）"""
    filtered_menus = mock_menus.copy()
    
    if status is not None:
        filtered_menus = [m for m in filtered_menus if m["status"] == status]
    
    # 构建树形结构
    menu_tree = build_menu_tree(filtered_menus)
    
    return MenuListResponse(
        code=200,
        msg="success",
        data=menu_tree
    )


@router.get("/simple", response_model=MenuSimpleResponse)
async def get_simple_menu_list():
    """获取简化菜单列表（用于选择）"""
    simple_menus = [
        {
            "id": m["id"],
            "parentId": m["parentId"],
            "menuName": m["menuName"],
            "menuType": m["menuType"]
        }
        for m in mock_menus
    ]
    
    return MenuSimpleResponse(
        code=200,
        msg="success",
        data=simple_menus
    )


@router.get("/{menu_id}")
async def get_menu(menu_id: int):
    """获取菜单详情"""
    menu = next((m for m in mock_menus if m["id"] == menu_id), None)
    if not menu:
        raise HTTPException(status_code=404, detail="菜单不存在")
    
    return {
        "code": 200,
        "msg": "success",
        "data": menu
    }


@router.post("")
async def create_menu(request: MenuCreateRequest):
    """创建菜单"""
    new_menu = {
        "id": len(mock_menus) + 1,
        "parentId": request.parentId,
        "menuName": request.menuName,
        "menuCode": request.menuCode,
        "menuType": request.menuType,
        "icon": request.icon,
        "path": request.path,
        "component": request.component,
        "permission": request.permission,
        "sort": request.sort,
        "status": request.status,
        "createTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    mock_menus.append(new_menu)
    
    return {
        "code": 200,
        "msg": "创建成功",
        "data": new_menu
    }


@router.put("/{menu_id}")
async def update_menu(menu_id: int, request: MenuUpdateRequest):
    """更新菜单"""
    menu = next((m for m in mock_menus if m["id"] == menu_id), None)
    if not menu:
        raise HTTPException(status_code=404, detail="菜单不存在")
    
    if request.parentId is not None:
        menu["parentId"] = request.parentId
    if request.menuName:
        menu["menuName"] = request.menuName
    if request.menuCode:
        menu["menuCode"] = request.menuCode
    if request.menuType is not None:
        menu["menuType"] = request.menuType
    if request.icon is not None:
        menu["icon"] = request.icon
    if request.path is not None:
        menu["path"] = request.path
    if request.component is not None:
        menu["component"] = request.component
    if request.permission is not None:
        menu["permission"] = request.permission
    if request.sort is not None:
        menu["sort"] = request.sort
    if request.status is not None:
        menu["status"] = request.status
    
    return {
        "code": 200,
        "msg": "更新成功",
        "data": menu
    }


@router.delete("/{menu_id}")
async def delete_menu(menu_id: int):
    """删除菜单"""
    global mock_menus
    menu = next((m for m in mock_menus if m["id"] == menu_id), None)
    if not menu:
        raise HTTPException(status_code=404, detail="菜单不存在")
    
    # 检查是否有子菜单
    children = [m for m in mock_menus if m["parentId"] == menu_id]
    if children:
        raise HTTPException(status_code=400, detail="该菜单下有子菜单，无法删除")
    
    mock_menus = [m for m in mock_menus if m["id"] != menu_id]
    
    return {
        "code": 200,
        "msg": "删除成功",
        "data": None
    }
