from pydantic import BaseModel
from typing import List, Optional


class UserInfo(BaseModel):
    """用户信息"""
    buttons: List[str]
    roles: List[str]
    userId: int
    userName: str
    email: str
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
