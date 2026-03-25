import random

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    extract_user_name_from_auth_header,
    hash_password,
    needs_password_upgrade,
    verify_password,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.base import BaseResponse
from app.schemas.user import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    ResetPasswordRequest,
    UserInfoResponse,
)

router = APIRouter(tags=["认证"])
verification_codes = {}

ROLE_MAP = {"super_admin": "R_SUPER", "admin": "R_ADMIN", "user": "R_USER"}
BUTTON_MAP = {
    "super_admin": ["add", "edit", "delete", "view"],
    "admin": ["add", "edit", "view"],
    "user": ["view"],
}


@router.post("/auth/login", response_model=BaseResponse[LoginResponse])
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """用户登录接口"""
    user = db.query(User).filter(User.userName == request.userName).first()
    if not user or not verify_password(request.password, user.password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    if needs_password_upgrade(user.password):
        user.password = hash_password(request.password)
        db.commit()

    return BaseResponse[LoginResponse](
        code=200,
        msg="登录成功",
        data=LoginResponse(
            token=create_access_token(user.userName),
            refreshToken=create_refresh_token(user.userName),
        ),
    )


@router.get("/auth/user/info", response_model=BaseResponse[UserInfoResponse])
def get_user_info(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    """获取用户信息接口"""
    user_name = extract_user_name_from_auth_header(authorization)
    user = db.query(User).filter(User.userName == user_name).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return BaseResponse[UserInfoResponse](
        code=200,
        msg="获取成功",
        data=UserInfoResponse(
            buttons=BUTTON_MAP.get(user.role, ["view"]),
            roles=[ROLE_MAP.get(user.role, "R_USER")],
            userId=user.id,
            userName=user.userName,
            email=user.email,
            userPhone=user.phone,
            avatar=None,
        ),
    )


@router.post("/auth/forgot-password", response_model=BaseResponse[dict])
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """忘记密码接口"""
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    verification_code = str(random.randint(100000, 999999))
    verification_codes[request.email] = verification_code
    return BaseResponse(code=200, msg="验证码已发送", data={"email": request.email})


@router.post("/auth/reset-password", response_model=BaseResponse[dict])
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """重置密码接口"""
    if (
        request.email not in verification_codes
        or verification_codes[request.email] != request.code
    ):
        raise HTTPException(status_code=400, detail="验证码错误")

    if request.newPassword != request.confirmPassword:
        raise HTTPException(status_code=400, detail="两次密码不一致")

    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user.password = hash_password(request.newPassword)
    db.commit()
    del verification_codes[request.email]
    return BaseResponse(code=200, msg="密码重置成功", data={"email": request.email})


@router.post("/auth/change-password", response_model=BaseResponse[dict])
def change_password(
    request: ChangePasswordRequest,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    """登录态修改密码接口"""
    user_name = extract_user_name_from_auth_header(authorization)
    user = db.query(User).filter(User.userName == user_name).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if not verify_password(request.currentPassword, user.password):
        raise HTTPException(status_code=400, detail="当前密码错误")

    if request.newPassword != request.confirmPassword:
        raise HTTPException(status_code=400, detail="两次密码不一致")

    user.password = hash_password(request.newPassword)
    db.commit()
    return BaseResponse(code=200, msg="密码修改成功", data={"userName": user.userName})
