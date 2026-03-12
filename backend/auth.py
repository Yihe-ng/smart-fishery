from pydantic import BaseModel
from typing import List,Optional
from model import RegisterRequest
class LoginRequest(BaseModel):
  """登录请求参数"""
  userName:str
  password:str  


class LoginResponse(BaseModel):
    """登录响应参数"""
    token:str
    refreshToken:str

class UserInfo(BaseModel):
    """用户信息"""
    button:List[str]
    roles:List[str]
    userId:int
    UserName:str
    email:str
    avater:Optional[str] = None

    
    



