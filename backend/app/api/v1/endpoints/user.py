from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreateRequest, UserUpdateRequest

router = APIRouter()

ROLE_TO_CODE = {"super_admin": "R_SUPER", "admin": "R_ADMIN", "user": "R_USER"}
CODE_TO_ROLE = {value: key for key, value in ROLE_TO_CODE.items()}


def normalize_status(value: Optional[str | int]) -> int:
    if value is None:
        return 1
    if isinstance(value, int):
        return value
    return 0 if str(value).strip() == "0" else 1


def resolve_role(role_codes: Optional[list[str]]) -> str:
    if not role_codes:
        return "user"
    return CODE_TO_ROLE.get(role_codes[0], "user")


def serialize_user(user: User) -> dict:
    create_time = user.createTime.strftime("%Y-%m-%d %H:%M:%S") if user.createTime else ""
    role_code = ROLE_TO_CODE.get(user.role or "user", "R_USER")
    return {
        "id": user.id,
        "avatar": "",
        "status": str(user.status),
        "userName": user.userName,
        "userGender": "",
        "nickName": user.userName,
        "userPhone": user.phone or "",
        "userEmail": user.email,
        "userRoles": [role_code],
        "createBy": "system",
        "createTime": create_time,
        "updateBy": "system",
        "updateTime": create_time,
    }


@router.get("/list")
def get_user_list(
    current: int = Query(1),
    size: int = Query(20),
    status: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    userEmail: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """获取用户列表"""
    query = db.query(User)
    if status is not None:
        query = query.filter(User.status == normalize_status(status))
    if keyword:
        query = query.filter(
            (User.userName.contains(keyword)) | (User.email.contains(keyword))
        )
    if userEmail:
        query = query.filter(User.email.contains(userEmail))

    total = query.count()
    users = query.offset((current - 1) * size).limit(size).all()
    return {
        "code": 200,
        "msg": "success",
        "data": {
            "list": [serialize_user(user) for user in users],
            "total": total,
            "current": current,
            "size": size,
        },
    }


@router.get("/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    """获取用户详情"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return {"code": 200, "msg": "success", "data": serialize_user(user)}


@router.post("")
def create_user(request: UserCreateRequest, db: Session = Depends(get_db)):
    """创建用户"""
    existing = db.query(User).filter(User.email == request.userEmail).first()
    if existing:
        raise HTTPException(status_code=400, detail="邮箱已存在")

    user = User(
        userName=request.userName,
        email=request.userEmail,
        phone=request.userPhone,
        password=hash_password(request.password or "123456"),
        status=normalize_status(request.status),
        role=resolve_role(request.userRoles),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"code": 200, "msg": "创建成功", "data": serialize_user(user)}


@router.put("/{user_id}")
def update_user(
    user_id: int,
    request: UserUpdateRequest,
    db: Session = Depends(get_db),
):
    """更新用户"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if request.userName:
        user.userName = request.userName
    if request.userEmail:
        existing = (
            db.query(User).filter(User.email == request.userEmail, User.id != user_id).first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="邮箱已被其他用户使用")
        user.email = request.userEmail
    if request.userPhone is not None:
        user.phone = request.userPhone
    if request.status is not None:
        user.status = normalize_status(request.status)
    if request.userRoles is not None:
        user.role = resolve_role(request.userRoles)

    db.commit()
    db.refresh(user)
    return {"code": 200, "msg": "更新成功", "data": serialize_user(user)}


@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """删除用户"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    db.delete(user)
    db.commit()
    return {"code": 200, "msg": "删除成功", "data": None}
