from fastapi import APIRouter, HTTPException
from app.schemas.user import (
    RegisterRequest, 
    LoginRequest, 
    LoginResponse, 
    UserInfoResponse, 
    ForgotPasswordRequest, 
    ResetPasswordRequest
)
from app.schemas.base import BaseResponse
import random

router = APIRouter(
    tags=["认证"]
)

@router.post("/auth/login", response_model=BaseResponse[LoginResponse])
def login(request: LoginRequest):
    """用户登录接口"""
    valid_users = {
        "Super": "123456",
        "Admin": "123456",
        "User": "123456",
    }

    if request.userName not in valid_users or valid_users[request.userName] != request.password:
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误"
        )
    return BaseResponse[LoginResponse](
        code=200,
        msg="登录成功",
        data=LoginResponse(
            token=f"mock_token_{request.userName}",
            refreshToken=f"mock_refresh_token_{request.userName}"
        )
    )

@router.post("/auth/register", response_model=BaseResponse[dict])
def register(request: RegisterRequest):
    """用户注册接口"""
    if request.password != request.confirmPassword:
        raise HTTPException(
            status_code=400,
            detail="两次输入密码不一致"
        )

    if not request.agreement:
        raise HTTPException(
            status_code=400,
            detail="请同意用户协议"
        )

    valid_users = {
        "Super": {
            "password": "123456",
            "email": "super@example.com"
        },
        "Admin": {
            "password": "123456",
            "email": "admin@example.com"
        },
        "User": {
            "password": "123456",
            "email": "user@example.com"
        },
    }

    if request.userName in valid_users:
        raise HTTPException(
            status_code=400,
            detail="用户名已存在"
        )

    for user_data in valid_users.values():
        if user_data["email"] == request.email:
            raise HTTPException(
                status_code=400,
                detail="该邮箱已被注册"
            )

    if "@" not in request.email:
        raise HTTPException(
            status_code=400,
            detail="邮箱格式不正确"
        )

    return BaseResponse(
        code=200,
        msg="注册成功",
        data={
            "userName": request.userName,
            "email": request.email
        }
    )

user_info_data = {
    "Super": {
        "buttons": ["add", "edit", "delete", "view"],
        "roles": ["R_SUPER"],
        "userId": 1,
        "userName": "Super",
        "email": "super@example.com",
        "avatar": None
    },
    "Admin": {
        "buttons": ["add", "edit", "view"],
        "roles": ["R_ADMIN"],
        "userId": 2,
        "userName": "Admin",
        "email": "admin@example.com",
        "avatar": None
    },
    "User": {
        "buttons": ["view"],
        "roles": ["R_USER"],
        "userId": 3,
        "userName": "User",
        "email": "user@example.com",
        "avatar": None
    }
}
verification_codes = {}

# 获取用户信息
@router.get("/auth/user/info", response_model=BaseResponse[UserInfoResponse])
def get_user_info():
    """获取用户信息接口"""
    user_info = user_info_data.get("Super")
    if not user_info:
        raise HTTPException(
            status_code=404,
            detail="用户不存在"
        )
    return BaseResponse[UserInfoResponse](
        code=200,
        msg="获取成功",
        data=UserInfoResponse(**user_info)
    )

# 忘记密码接口
@router.post("/auth/forgot-password", response_model=BaseResponse[dict])
def forgot_password(request: ForgotPasswordRequest):
    """忘记密码接口"""
    user_found = False
    for user_data in user_info_data.values():
        if user_data["email"] == request.email:
            user_found = True
            break

    if not user_found:
        raise HTTPException(
            status_code=404,
            detail="用户不存在"
        )
    
    verification_code = str(random.randint(100000, 999999))
    verification_codes[request.email] = verification_code
    
    print(f"验证码已发送到邮箱: {request.email}，验证码: {verification_code}")
    
    return BaseResponse(
        code=200,
        msg="验证码已发送",
        data={"email": request.email}
    )

# 重置密码接口
@router.post("/auth/reset-password", response_model=BaseResponse[dict])
def reset_password(request: ResetPasswordRequest):
    """重置密码接口"""
    if request.email not in verification_codes or verification_codes[request.email] != request.code:
        raise HTTPException(status_code=400, detail="验证码错误")
    
    if request.newPassword != request.confirmPassword:
        raise HTTPException(status_code=400, detail="两次密码不一致")
    
    for user_name, user_data in user_info_data.items():
        if user_data["email"] == request.email:
            user_info_data[user_name]["password"] = request.newPassword
            break
    
    del verification_codes[request.email]
    
    return BaseResponse(
        code=200,
        msg="密码重置成功",
        data={"email": request.email}
    )
