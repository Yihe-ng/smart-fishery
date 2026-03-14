from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class UserListItem(BaseModel):
    """用户列表项"""
    id: int
    userName: str
    email: str
    phone: Optional[str] = None
    status: int  # 1: 启用, 0: 禁用
    createTime: str
    roleNames: List[str] = []


class UserListResponse(BaseModel):
    """用户列表响应"""
    code: int
    msg: str
    data: dict


class UserCreateRequest(BaseModel):
    """创建用户请求"""
    userName: str
    email: str
    phone: Optional[str] = None
    password: str
    roleIds: List[int] = []
    status: int = 1


class UserUpdateRequest(BaseModel):
    """更新用户请求"""
    userName: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    roleIds: Optional[List[int]] = None
    status: Optional[int] = None


@router.get("/list", response_model=UserListResponse)
async def get_user_list(
    current: int = Query(1, description="当前页码"),
    size: int = Query(20, description="每页大小"),
    status: Optional[int] = Query(None, description="状态筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索")
):
    """获取用户列表"""
    # 模拟数据
    mock_users = [
        {
            "id": 1,
            "userName": "admin",
            "email": "admin@example.com",
            "phone": "13800138000",
            "status": 1,
            "createTime": "2024-01-01 00:00:00",
            "roleNames": ["管理员"]
        },
        {
            "id": 2,
            "userName": "user1",
            "email": "user1@example.com",
            "phone": "13800138001",
            "status": 1,
            "createTime": "2024-01-02 00:00:00",
            "roleNames": ["普通用户"]
        },
        {
            "id": 3,
            "userName": "user2",
            "email": "user2@example.com",
            "phone": "13800138002",
            "status": 0,
            "createTime": "2024-01-03 00:00:00",
            "roleNames": ["普通用户"]
        }
    ]
    
    # 状态筛选
    if status is not None:
        mock_users = [user for user in mock_users if user["status"] == status]
    
    # 关键词搜索
    if keyword:
        mock_users = [
            user for user in mock_users
            if keyword.lower() in user["userName"].lower() or keyword.lower() in user["email"].lower()
        ]
    
    total = len(mock_users)
    
    # 分页
    start = (current - 1) * size
    end = start + size
    page_data = mock_users[start:end]
    
    return UserListResponse(
        code=200,
        msg="success",
        data={
            "list": page_data,
            "total": total,
            "current": current,
            "size": size
        }
    )


@router.get("/{user_id}")
async def get_user(user_id: int):
    """获取用户详情"""
    # 模拟数据
    mock_users = [
        {
            "id": 1,
            "userName": "admin",
            "email": "admin@example.com",
            "phone": "13800138000",
            "status": 1,
            "createTime": "2024-01-01 00:00:00",
            "roleNames": ["管理员"]
        },
        {
            "id": 2,
            "userName": "user1",
            "email": "user1@example.com",
            "phone": "13800138001",
            "status": 1,
            "createTime": "2024-01-02 00:00:00",
            "roleNames": ["普通用户"]
        },
        {
            "id": 3,
            "userName": "user2",
            "email": "user2@example.com",
            "phone": "13800138002",
            "status": 0,
            "createTime": "2024-01-03 00:00:00",
            "roleNames": ["普通用户"]
        }
    ]
    
    user = next((u for u in mock_users if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return {
        "code": 200,
        "msg": "success",
        "data": user
    }


@router.post("")
async def create_user(request: UserCreateRequest):
    """创建用户"""
    # 模拟数据
    mock_users = [
        {"id": 1, "email": "admin@example.com"},
        {"id": 2, "email": "user1@example.com"},
        {"id": 3, "email": "user2@example.com"}
    ]
    
    # 检查邮箱是否已存在
    existing_user = next((u for u in mock_users if u["email"] == request.email), None)
    if existing_user:
        raise HTTPException(status_code=400, detail="邮箱已存在")
    
    # 模拟密码处理
    hashed_password = f"hashed_{request.password}"
    
    # 模拟创建新用户
    new_user = {
        "id": 4,
        "userName": request.userName,
        "email": request.email,
        "phone": request.phone,
        "status": request.status,
        "createTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "roleNames": ["普通用户"]
    }
    
    return {
        "code": 200,
        "msg": "创建成功",
        "data": new_user
    }


@router.put("/{user_id}")
async def update_user(user_id: int, request: UserUpdateRequest):
    """更新用户"""
    # 模拟数据
    mock_users = [
        {
            "id": 1,
            "userName": "admin",
            "email": "admin@example.com",
            "phone": "13800138000",
            "status": 1,
            "createTime": "2024-01-01 00:00:00",
            "roleNames": ["管理员"]
        },
        {
            "id": 2,
            "userName": "user1",
            "email": "user1@example.com",
            "phone": "13800138001",
            "status": 1,
            "createTime": "2024-01-02 00:00:00",
            "roleNames": ["普通用户"]
        },
        {
            "id": 3,
            "userName": "user2",
            "email": "user2@example.com",
            "phone": "13800138002",
            "status": 0,
            "createTime": "2024-01-03 00:00:00",
            "roleNames": ["普通用户"]
        }
    ]
    
    user = next((u for u in mock_users if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 检查邮箱是否已被其他用户使用
    if request.email:
        existing_user = next((u for u in mock_users if u["email"] == request.email and u["id"] != user_id), None)
        if existing_user:
            raise HTTPException(status_code=400, detail="邮箱已被其他用户使用")
    
    # 更新字段
    if request.userName:
        user["userName"] = request.userName
    if request.email:
        user["email"] = request.email
    if request.phone:
        user["phone"] = request.phone
    if request.status is not None:
        user["status"] = request.status
    
    return {
        "code": 200,
        "msg": "更新成功",
        "data": user
    }


@router.delete("/{user_id}")
async def delete_user(user_id: int):
    """删除用户"""
    # 模拟数据
    mock_users = [
        {"id": 1}, {"id": 2}, {"id": 3}
    ]
    
    user = next((u for u in mock_users if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return {
        "code": 200,
        "msg": "删除成功",
        "data": None
    }
