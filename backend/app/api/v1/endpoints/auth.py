from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.schemas.user import (
    LoginRequest,
    LoginResponse,
    UserInfoResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.schemas.base import BaseResponse
from app.db.session import get_db
from app.models.user import User
import random

router = APIRouter(tags=["认证"])
verification_codes = {}


@router.post("/auth/login", response_model=BaseResponse[LoginResponse])
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """用户登录接口"""
    user = db.query(User).filter(User.userName == request.userName).first()
    if not user or user.password != request.password:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    return BaseResponse[LoginResponse](
        code=200,
        msg="登录成功",
        data=LoginResponse(
            token=f"mock_token_{request.userName}",
            refreshToken=f"mock_refresh_token_{request.userName}",
        ),
    )


@router.get("/auth/user/info", response_model=BaseResponse[UserInfoResponse])
def get_user_info(db: Session = Depends(get_db)):
    """获取用户信息接口"""
    user = db.query(User).filter(User.userName == "Super").first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    role_map = {"super_admin": "R_SUPER", "admin": "R_ADMIN", "user": "R_USER"}
    button_map = {
        "super_admin": ["add", "edit", "delete", "view"],
        "admin": ["add", "edit", "view"],
        "user": ["view"],
    }
    return BaseResponse[UserInfoResponse](
        code=200,
        msg="获取成功",
        data=UserInfoResponse(
            buttons=button_map.get(user.role, ["view"]),
            roles=[role_map.get(user.role, "R_USER")],
            userId=user.id,
            userName=user.userName,
            email=user.email,
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
    if user:
        user.password = request.newPassword
        db.commit()
    del verification_codes[request.email]
    return BaseResponse(code=200, msg="密码重置成功", data={"email": request.email})
