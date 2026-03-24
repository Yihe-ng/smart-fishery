from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class UserInfo(BaseModel):
    """用户信息"""

    buttons: List[str]
    roles: List[str]
    userId: int
    userName: str
    email: str
    userPhone: Optional[str] = None
    avatar: Optional[str] = None


class LoginRequest(BaseModel):
    """登录请求参数"""

    userName: str
    password: str


class RegisterRequest(BaseModel):
    """注册请求参数"""

    userName: str
    email: str
    password: str
    confirmPassword: str
    agreement: bool


class LoginResponse(BaseModel):
    """登录响应数据"""

    token: str
    refreshToken: str


class UserInfoResponse(BaseModel):
    """用户信息响应"""

    buttons: List[str]
    roles: List[str]
    userId: int
    userName: str
    email: str
    userPhone: Optional[str] = None
    avatar: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    """忘记密码请求"""

    email: str


class ResetPasswordRequest(BaseModel):
    """重置密码请求"""

    email: str
    code: str
    newPassword: str
    confirmPassword: str


class ChangePasswordRequest(BaseModel):
    currentPassword: str
    newPassword: str
    confirmPassword: str


class UserCreateRequest(BaseModel):
    userName: str
    userEmail: str
    userPhone: Optional[str] = None
    userGender: Optional[str] = None
    userRoles: List[str] = []
    password: Optional[str] = None
    status: Optional[str] = "1"


class UserUpdateRequest(BaseModel):
    userName: Optional[str] = None
    userEmail: Optional[str] = None
    userPhone: Optional[str] = None
    userGender: Optional[str] = None
    userRoles: Optional[List[str]] = None
    status: Optional[str] = None


class UserResponse(BaseModel):
    """用户列表响应"""

    id: int
    userName: str
    email: str
    phone: Optional[str] = None
    status: int
    role: Optional[str] = None
    createTime: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
