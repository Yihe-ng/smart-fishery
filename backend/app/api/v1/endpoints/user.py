from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from typing import Optional
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter()


@router.get("/list")
def get_user_list(
    current: int = Query(1),
    size: int = Query(20),
    status: Optional[int] = Query(None),
    keyword: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """获取用户列表"""
    query = db.query(User)
    if status is not None:
        query = query.filter(User.status == status)
    if keyword:
        query = query.filter(
            (User.userName.contains(keyword)) | (User.email.contains(keyword))
        )
    total = query.count()
    users = query.offset((current - 1) * size).limit(size).all()
    user_list = [UserResponse.model_validate(u).model_dump() for u in users]
    for u in user_list:
        if u.get("createTime"):
            u["createTime"] = u["createTime"].strftime("%Y-%m-%d %H:%M:%S")
        u["roleNames"] = [u.get("role", "")]
    return {
        "code": 200,
        "msg": "success",
        "data": {"list": user_list, "total": total, "current": current, "size": size},
    }


@router.get("/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    """获取用户详情"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user_data = UserResponse.model_validate(user).model_dump()
    if user_data.get("createTime"):
        user_data["createTime"] = user_data["createTime"].strftime("%Y-%m-%d %H:%M:%S")
    user_data["roleNames"] = [user_data.get("role", "")]
    return {"code": 200, "msg": "success", "data": user_data}


@router.post("")
def create_user(
    userName: str,
    email: str,
    password: str,
    phone: str = None,
    status: int = 1,
    db: Session = Depends(get_db),
):
    """创建用户"""
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="邮箱已存在")
    user = User(
        userName=userName,
        email=email,
        phone=phone,
        password=f"hashed_{password}",
        status=status,
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {
        "code": 200,
        "msg": "创建成功",
        "data": {"id": user.id, "userName": user.userName, "email": user.email},
    }


@router.put("/{user_id}")
def update_user(
    user_id: int,
    userName: str = None,
    email: str = None,
    phone: str = None,
    status: int = None,
    db: Session = Depends(get_db),
):
    """更新用户"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if userName:
        user.userName = userName
    if email:
        existing = (
            db.query(User).filter(User.email == email, User.id != user_id).first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="邮箱已被其他用户使用")
        user.email = email
    if phone:
        user.phone = phone
    if status is not None:
        user.status = status
    db.commit()
    return {
        "code": 200,
        "msg": "更新成功",
        "data": {"id": user.id, "userName": user.userName},
    }


@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """删除用户"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    db.delete(user)
    db.commit()
    return {"code": 200, "msg": "删除成功", "data": None}
