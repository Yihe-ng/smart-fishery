from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy.orm import Session
from db.session import get_db
from models.user import User
from passlib.context import CryptContext

router = APIRouter()

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    db: Session = Depends(get_db)
):
    """获取用户列表"""
    # 构建查询
    query = db.query(User)
    
    # 状态筛选
    if status is not None:
        query = query.filter(User.status == status)
    
    # 关键词搜索
    if keyword:
        query = query.filter(
            (User.userName.ilike(f"%{keyword}%") ) |
            (User.email.ilike(f"%{keyword}%") )
        )
    
    # 获取总数
    total = query.count()
    
    # 分页
    start = (current - 1) * size
    end = start + size
    users = query.offset(start).limit(size).all()
    
    # 转换为响应格式
    page_data = []
    for user in users:
        user_dict = {
            "id": user.id,
            "userName": user.userName,
            "email": user.email,
            "phone": user.phone,
            "status": user.status,
            "createTime": user.createTime.strftime("%Y-%m-%d %H:%M:%S"),
            "roleNames": ["普通用户"]  # 简化处理
        }
        page_data.append(user_dict)
    
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
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """获取用户详情"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    user_dict = {
        "id": user.id,
        "userName": user.userName,
        "email": user.email,
        "phone": user.phone,
        "status": user.status,
        "createTime": user.createTime.strftime("%Y-%m-%d %H:%M:%S"),
        "roleNames": ["普通用户"]  # 简化处理
    }
    
    return {
        "code": 200,
        "msg": "success",
        "data": user_dict
    }


@router.post("")
async def create_user(request: UserCreateRequest, db: Session = Depends(get_db)):
    """创建用户"""
    # 检查邮箱是否已存在
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="邮箱已存在")
    
    # 加密密码
    hashed_password = pwd_context.hash(request.password)
    
    # 创建新用户
    new_user = User(
        userName=request.userName,
        email=request.email,
        phone=request.phone,
        password=hashed_password,
        status=request.status
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    user_dict = {
        "id": new_user.id,
        "userName": new_user.userName,
        "email": new_user.email,
        "phone": new_user.phone,
        "status": new_user.status,
        "createTime": new_user.createTime.strftime("%Y-%m-%d %H:%M:%S"),
        "roleNames": ["普通用户"]  # 简化处理
    }
    
    return {
        "code": 200,
        "msg": "创建成功",
        "data": user_dict
    }


@router.put("/{user_id}")
async def update_user(user_id: int, request: UserUpdateRequest, db: Session = Depends(get_db)):
    """更新用户"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 更新字段
    if request.userName:
        user.userName = request.userName
    if request.email:
        # 检查邮箱是否已被其他用户使用
        existing_user = db.query(User).filter(
            User.email == request.email, 
            User.id != user_id
        ).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="邮箱已被其他用户使用")
        user.email = request.email
    if request.phone:
        user.phone = request.phone
    if request.status is not None:
        user.status = request.status
    
    db.commit()
    db.refresh(user)
    
    user_dict = {
        "id": user.id,
        "userName": user.userName,
        "email": user.email,
        "phone": user.phone,
        "status": user.status,
        "createTime": user.createTime.strftime("%Y-%m-%d %H:%M:%S"),
        "roleNames": ["普通用户"]  # 简化处理
    }
    
    return {
        "code": 200,
        "msg": "更新成功",
        "data": user_dict
    }


@router.delete("/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    """删除用户"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    db.delete(user)
    db.commit()
    
    return {
        "code": 200,
        "msg": "删除成功",
        "data": None
    }
