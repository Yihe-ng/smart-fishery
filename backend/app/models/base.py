from pydantic import BaseModel
from typing import Generic, TypeVar,Optional,List

T = TypeVar('T')

class BaseResponse(BaseModel, Generic[T]):
    """统一API格式"""
    code: int
    msg: str
    data: T

#分页功能实现
class PageQuery(BaseModel):
    """分页查询参数"""
    pageNum: int = 1
    pageSize: int = 10   #每页规定数据数目
    keyword: Optional[str] = None    #默认为NONE
    
class PageResult(BaseModel,Generic[T]):
    """分页结果"""
    total: int 
    list: List[T] = []
