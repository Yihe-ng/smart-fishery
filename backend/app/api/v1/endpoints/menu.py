from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.menu import Menu

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
    roles: Optional[List[str]] = None
    keepAlive: Optional[bool] = None
    isHide: Optional[bool] = None
    isHideTab: Optional[bool] = None
    link: Optional[str] = None
    isIframe: Optional[bool] = None
    showBadge: Optional[bool] = None
    showTextBadge: Optional[str] = None
    fixedTab: Optional[bool] = None
    activePath: Optional[str] = None
    isFullPage: Optional[bool] = None
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
    roles: Optional[List[str]] = None
    keepAlive: Optional[bool] = None
    isHide: Optional[bool] = None
    isHideTab: Optional[bool] = None
    link: Optional[str] = None
    isIframe: Optional[bool] = None
    showBadge: Optional[bool] = None
    showTextBadge: Optional[str] = None
    fixedTab: Optional[bool] = None
    activePath: Optional[str] = None
    isFullPage: Optional[bool] = None


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
    roles: Optional[List[str]] = None
    keepAlive: Optional[bool] = None
    isHide: Optional[bool] = None
    isHideTab: Optional[bool] = None
    link: Optional[str] = None
    isIframe: Optional[bool] = None
    showBadge: Optional[bool] = None
    showTextBadge: Optional[str] = None
    fixedTab: Optional[bool] = None
    activePath: Optional[str] = None
    isFullPage: Optional[bool] = None


# 首次启动种子菜单：与前端路由模块（src/router/modules/fishery.ts、system.ts）保持一致。
# menuName 存 i18n key，前端 formatMenuTitle 解析为当前语言文案；按钮项存原文。
# 数据首次写入 SQLite 后，菜单管理的增删改会持久化，不再依赖进程内 mock。
mock_menus = [
    # ── 石斑鱼智慧监测 ──
    {
        "id": 1,
        "parentId": 0,
        "menuName": "menus.fishery.title",
        "menuCode": "Fishery",
        "menuType": 1,
        "icon": "ri:water-flash-line",
        "path": "/fishery",
        "component": "/index/index",
        "permission": None,
        "sort": 1,
        "status": 1,
        "createTime": "2026-08-08 10:00:00",
        "roles": ["R_SUPER", "R_ADMIN", "R_USER"],
    },
    {
        "id": 2,
        "parentId": 1,
        "menuName": "menus.fishery.dashboard",
        "menuCode": "FisheryDashboard",
        "menuType": 2,
        "icon": "ri:dashboard-line",
        "path": "dashboard",
        "component": "/dashboard/fishery-console/index",
        "permission": None,
        "sort": 1,
        "status": 1,
        "createTime": "2026-08-08 10:00:00",
        "keepAlive": True,
    },
    {
        "id": 3,
        "parentId": 1,
        "menuName": "menus.fishery.growth",
        "menuCode": "GrowthRecognition",
        "menuType": 2,
        "icon": "ri:scales-3-line",
        "path": "growth",
        "component": "/growth-monitoring/detect/index",
        "permission": None,
        "sort": 2,
        "status": 1,
        "createTime": "2026-08-08 10:00:00",
        "keepAlive": True,
    },
    {
        "id": 4,
        "parentId": 1,
        "menuName": "menus.fishery.growthRecords",
        "menuCode": "GrowthRecords",
        "menuType": 2,
        "icon": "ri:file-list-3-line",
        "path": "growth-records",
        "component": "/growth-monitoring/records/index",
        "permission": None,
        "sort": 3,
        "status": 1,
        "createTime": "2026-08-16 10:00:00",
        "keepAlive": True,
    },
    {
        "id": 5,
        "parentId": 1,
        "menuName": "menus.fishery.feeding",
        "menuCode": "Feeding",
        "menuType": 2,
        "icon": "ri:hand-coin-line",
        "path": "feeding",
        "component": "/feeding/index",
        "permission": None,
        "sort": 4,
        "status": 1,
        "createTime": "2026-08-08 10:00:00",
        "keepAlive": True,
    },
    {
        "id": 7,
        "parentId": 1,
        "menuName": "menus.fishery.waterQuality",
        "menuCode": "WaterQuality",
        "menuType": 2,
        "icon": "ri:temp-hot-line",
        "path": "water-quality",
        "component": "/monitoring/water-quality/index",
        "permission": None,
        "sort": 6,
        "status": 1,
        "createTime": "2026-08-08 10:00:00",
        "keepAlive": True,
        "isHide": True,
    },
    {
        "id": 8,
        "parentId": 1,
        "menuName": "menus.fishery.production",
        "menuCode": "Production",
        "menuType": 2,
        "icon": "ri:bar-chart-box-line",
        "path": "production",
        "component": "/production/index",
        "permission": None,
        "sort": 7,
        "status": 1,
        "createTime": "2026-08-08 10:00:00",
        "keepAlive": True,
        "isHide": True,
    },
    # ── 系统管理 ──
    {
        "id": 10,
        "parentId": 0,
        "menuName": "menus.system.title",
        "menuCode": "System",
        "menuType": 1,
        "icon": "ri:user-3-line",
        "path": "/system",
        "component": "/index/index",
        "permission": None,
        "sort": 2,
        "status": 1,
        "createTime": "2026-08-08 10:00:00",
        "roles": ["R_SUPER", "R_ADMIN"],
    },
    {
        "id": 11,
        "parentId": 10,
        "menuName": "menus.system.user",
        "menuCode": "User",
        "menuType": 2,
        "icon": None,
        "path": "user",
        "component": "/system/user",
        "permission": None,
        "sort": 1,
        "status": 1,
        "createTime": "2026-08-08 10:00:00",
        "roles": ["R_SUPER", "R_ADMIN"],
        "keepAlive": True,
    },
    {
        "id": 12,
        "parentId": 10,
        "menuName": "menus.system.role",
        "menuCode": "Role",
        "menuType": 2,
        "icon": None,
        "path": "role",
        "component": "/system/role",
        "permission": None,
        "sort": 2,
        "status": 1,
        "createTime": "2026-08-08 10:00:00",
        "roles": ["R_SUPER"],
        "keepAlive": True,
    },
    {
        "id": 13,
        "parentId": 10,
        "menuName": "menus.system.menu",
        "menuCode": "Menus",
        "menuType": 2,
        "icon": None,
        "path": "menu",
        "component": "/system/menu",
        "permission": None,
        "sort": 3,
        "status": 1,
        "createTime": "2026-08-08 10:00:00",
        "roles": ["R_SUPER", "R_ADMIN"],
        "keepAlive": True,
    },
    {
        "id": 14,
        "parentId": 13,
        "menuName": "新增",
        "menuCode": "Menus_add",
        "menuType": 3,
        "icon": None,
        "path": None,
        "component": None,
        "permission": "add",
        "sort": 1,
        "status": 1,
        "createTime": "2026-08-08 10:00:00",
    },
    {
        "id": 15,
        "parentId": 13,
        "menuName": "编辑",
        "menuCode": "Menus_edit",
        "menuType": 3,
        "icon": None,
        "path": None,
        "component": None,
        "permission": "edit",
        "sort": 2,
        "status": 1,
        "createTime": "2026-08-08 10:00:00",
    },
    {
        "id": 16,
        "parentId": 13,
        "menuName": "删除",
        "menuCode": "Menus_delete",
        "menuType": 3,
        "icon": None,
        "path": None,
        "component": None,
        "permission": "delete",
        "sort": 3,
        "status": 1,
        "createTime": "2026-08-08 10:00:00",
    },
    {
        "id": 17,
        "parentId": 10,
        "menuName": "menus.system.userCenter",
        "menuCode": "UserCenter",
        "menuType": 2,
        "icon": None,
        "path": "user-center",
        "component": "/system/user-center",
        "permission": None,
        "sort": 4,
        "status": 1,
        "createTime": "2026-08-08 10:00:00",
        "keepAlive": True,
        "isHide": True,
        "isHideTab": True,
    },
]


def _menu_to_dict(menu: Menu) -> dict:
    """将 ORM 菜单转换为前后端共用的驼峰响应结构。"""
    return {
        "id": menu.id,
        "parentId": menu.parent_id,
        "menuName": menu.menu_name,
        "menuCode": menu.menu_code,
        "menuType": menu.menu_type,
        "icon": menu.icon,
        "path": menu.path,
        "component": menu.component,
        "permission": menu.permission,
        "sort": menu.sort,
        "status": menu.status,
        "createTime": menu.create_time.strftime("%Y-%m-%d %H:%M:%S")
        if menu.create_time
        else datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "roles": menu.role_list(),
        "keepAlive": menu.keep_alive,
        "isHide": menu.is_hide,
        "isHideTab": menu.is_hide_tab,
        "link": menu.link,
        "isIframe": menu.is_iframe,
        "showBadge": menu.show_badge,
        "showTextBadge": menu.show_text_badge,
        "fixedTab": menu.fixed_tab,
        "activePath": menu.active_path,
        "isFullPage": menu.is_full_page,
    }


def build_menu_tree(menus: List[dict], parent_id: int = 0) -> List[dict]:
    """构建菜单树，避免修改 ORM 映射出的原始节点。"""
    tree = []
    for menu in menus:
        if menu["parentId"] != parent_id:
            continue
        node = dict(menu)
        children = build_menu_tree(menus, menu["id"])
        if children:
            node["children"] = children
        tree.append(node)
    return tree


def _seed_menus(db: Session) -> None:
    """数据库为空时写入一次内置菜单；已有数据不被启动流程覆盖。"""
    if db.query(Menu.id).first() is not None:
        return

    for item in mock_menus:
        db.add(
            Menu(
                id=item["id"],
                parent_id=item["parentId"],
                menu_name=item["menuName"],
                menu_code=item["menuCode"],
                menu_type=item["menuType"],
                icon=item.get("icon"),
                path=item.get("path"),
                component=item.get("component"),
                permission=item.get("permission"),
                sort=item.get("sort", 0),
                status=item.get("status", 1),
                roles=item.get("roles"),
                keep_alive=item.get("keepAlive"),
                is_hide=item.get("isHide"),
                is_hide_tab=item.get("isHideTab"),
                link=item.get("link"),
                is_iframe=item.get("isIframe"),
                show_badge=item.get("showBadge"),
                show_text_badge=item.get("showTextBadge"),
                fixed_tab=item.get("fixedTab"),
                active_path=item.get("activePath"),
                is_full_page=item.get("isFullPage"),
                create_time=datetime.strptime(item["createTime"], "%Y-%m-%d %H:%M:%S"),
            )
        )
    db.commit()


@router.get("/list", response_model=MenuListResponse)
async def get_menu_list(
    status: Optional[int] = Query(None, description="状态筛选"),
    db: Session = Depends(get_db),
):
    """获取菜单列表（树形结构）"""
    _seed_menus(db)
    query = db.query(Menu)
    if status is not None:
        query = query.filter(Menu.status == status)

    rows = query.order_by(Menu.parent_id, Menu.sort, Menu.id).all()
    menu_tree = build_menu_tree([_menu_to_dict(row) for row in rows])
    
    return MenuListResponse(
        code=200,
        msg="success",
        data=menu_tree
    )


@router.get("/simple", response_model=MenuSimpleResponse)
async def get_simple_menu_list(db: Session = Depends(get_db)):
    """获取简化菜单列表（用于选择）"""
    _seed_menus(db)
    simple_menus = [
        {
            "id": m.id,
            "parentId": m.parent_id,
            "menuName": m.menu_name,
            "menuType": m.menu_type,
        }
        for m in db.query(Menu).order_by(Menu.parent_id, Menu.sort, Menu.id).all()
    ]
    
    return MenuSimpleResponse(
        code=200,
        msg="success",
        data=simple_menus
    )


@router.get("/{menu_id}")
async def get_menu(menu_id: int, db: Session = Depends(get_db)):
    """获取菜单详情"""
    _seed_menus(db)
    menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if not menu:
        raise HTTPException(status_code=404, detail="菜单不存在")

    return {
        "code": 200,
        "msg": "success",
        "data": _menu_to_dict(menu),
    }


@router.post("")
async def create_menu(request: MenuCreateRequest, db: Session = Depends(get_db)):
    """创建菜单"""
    _seed_menus(db)
    if request.parentId and not db.query(Menu.id).filter(Menu.id == request.parentId).first():
        raise HTTPException(status_code=400, detail="父级菜单不存在")

    new_menu = {
        "parent_id": request.parentId,
        "menu_name": request.menuName,
        "menu_code": request.menuCode,
        "menu_type": request.menuType,
        "icon": request.icon,
        "path": request.path,
        "component": request.component,
        "permission": request.permission,
        "sort": request.sort,
        "status": request.status,
        "roles": request.roles,
        "keep_alive": request.keepAlive,
        "is_hide": request.isHide,
        "is_hide_tab": request.isHideTab,
        "link": request.link,
        "is_iframe": request.isIframe,
        "show_badge": request.showBadge,
        "show_text_badge": request.showTextBadge,
        "fixed_tab": request.fixedTab,
        "active_path": request.activePath,
        "is_full_page": request.isFullPage,
    }
    db_menu = Menu(**new_menu)
    db.add(db_menu)
    db.commit()
    db.refresh(db_menu)

    return {
        "code": 200,
        "msg": "创建成功",
        "data": _menu_to_dict(db_menu),
    }


@router.put("/{menu_id}")
async def update_menu(
    menu_id: int, request: MenuUpdateRequest, db: Session = Depends(get_db)
):
    """更新菜单"""
    _seed_menus(db)
    menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if not menu:
        raise HTTPException(status_code=404, detail="菜单不存在")

    if "parentId" in request.model_fields_set:
        if request.parentId and not db.query(Menu.id).filter(Menu.id == request.parentId).first():
            raise HTTPException(status_code=400, detail="父级菜单不存在")
        menu.parent_id = request.parentId or 0

    field_map = {
        "menuName": "menu_name",
        "menuCode": "menu_code",
        "menuType": "menu_type",
        "icon": "icon",
        "path": "path",
        "component": "component",
        "permission": "permission",
        "sort": "sort",
        "status": "status",
        "roles": "roles",
        "keepAlive": "keep_alive",
        "isHide": "is_hide",
        "isHideTab": "is_hide_tab",
        "link": "link",
        "isIframe": "is_iframe",
        "showBadge": "show_badge",
        "showTextBadge": "show_text_badge",
        "fixedTab": "fixed_tab",
        "activePath": "active_path",
        "isFullPage": "is_full_page",
    }
    for request_name, model_name in field_map.items():
        if request_name in request.model_fields_set:
            setattr(menu, model_name, getattr(request, request_name))

    db.commit()
    db.refresh(menu)

    return {
        "code": 200,
        "msg": "更新成功",
        "data": _menu_to_dict(menu),
    }


@router.delete("/{menu_id}")
async def delete_menu(menu_id: int, db: Session = Depends(get_db)):
    """删除菜单"""
    _seed_menus(db)
    menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if not menu:
        raise HTTPException(status_code=404, detail="菜单不存在")

    # 检查是否有子菜单
    if db.query(Menu.id).filter(Menu.parent_id == menu_id).first():
        raise HTTPException(status_code=400, detail="该菜单下有子菜单，无法删除")

    db.delete(menu)
    db.commit()

    return {
        "code": 200,
        "msg": "删除成功",
        "data": None,
    }
