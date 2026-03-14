from fastapi import APIRouter, HTTPException, Query
from app.schemas.base import BaseResponse, PageQuery, PageResult
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter()


class FishPondBase(BaseModel):
    """鱼塘基础模型"""
    name: str
    code: str
    volume: float
    fish_type: str
    fish_count: int
    status: str


class FishPondCreate(FishPondBase):
    """创建鱼塘模型"""
    remark: Optional[str] = None


class FishPondUpdate(BaseModel):
    """更新鱼塘模型"""
    name: Optional[str] = None
    code: Optional[str] = None
    volume: Optional[float] = None
    fish_type: Optional[str] = None
    fish_count: Optional[int] = None
    status: Optional[str] = None
    remark: Optional[str] = None


class FishPondResponse(FishPondBase):
    """鱼塘响应模型"""
    id: str
    create_time: str
    update_time: str
    remark: Optional[str] = None


# 模拟鱼塘数据
mock_ponds = [
    {
        "id": "1",
        "name": "试验池 A",
        "code": "P001",
        "volume": 500.0,
        "fish_type": "石斑鱼",
        "fish_count": 1000,
        "status": "running",
        "create_time": "2024-01-01 00:00:00",
        "update_time": "2024-01-01 00:00:00",
        "remark": "主试验池"
    },
    {
        "id": "2",
        "name": "试验池 B",
        "code": "P002",
        "volume": 300.0,
        "fish_type": "石斑鱼",
        "fish_count": 600,
        "status": "running",
        "create_time": "2024-01-02 00:00:00",
        "update_time": "2024-01-02 00:00:00",
        "remark": "备用试验池"
    },
    {
        "id": "3",
        "name": "试验池 C",
        "code": "P003",
        "volume": 400.0,
        "fish_type": "石斑鱼",
        "fish_count": 800,
        "status": "maintenance",
        "create_time": "2024-01-03 00:00:00",
        "update_time": "2024-01-03 00:00:00",
        "remark": "维护中"
    }
]


@router.get("/list", response_model=BaseResponse[PageResult[FishPondResponse]])
def get_pond_list(
    pageNum: int = Query(1, description="当前页码"),
    pageSize: int = Query(10, description="每页大小"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    status: Optional[str] = Query(None, description="状态筛选")
):
    """获取鱼塘列表"""
    filtered_ponds = mock_ponds.copy()
    
    if status:
        filtered_ponds = [p for p in filtered_ponds if p["status"] == status]
    
    if keyword:
        filtered_ponds = [
            p for p in filtered_ponds
            if keyword.lower() in p["name"].lower() or keyword.lower() in p["code"].lower()
        ]
    
    total = len(filtered_ponds)
    start = (pageNum - 1) * pageSize
    end = start + pageSize
    page_data = filtered_ponds[start:end]
    
    return BaseResponse[PageResult[FishPondResponse]](
        code=200,
        msg="获取成功",
        data=PageResult[FishPondResponse](
            total=total,
            list=[FishPondResponse(**pond) for pond in page_data]
        )
    )


@router.get("/detail/{pond_id}", response_model=BaseResponse[FishPondResponse])
def get_pond_detail(pond_id: str):
    """获取鱼塘详情"""
    pond = next((p for p in mock_ponds if p["id"] == pond_id), None)
    if not pond:
        raise HTTPException(status_code=404, detail="鱼塘不存在")
    
    return BaseResponse[FishPondResponse](
        code=200,
        msg="获取成功",
        data=FishPondResponse(**pond)
    )


@router.post("/create", response_model=BaseResponse[FishPondResponse])
def create_pond(data: FishPondCreate):
    """创建鱼塘"""
    new_pond = {
        "id": str(len(mock_ponds) + 1),
        "name": data.name,
        "code": data.code,
        "volume": data.volume,
        "fish_type": data.fish_type,
        "fish_count": data.fish_count,
        "status": data.status,
        "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "remark": data.remark
    }
    mock_ponds.append(new_pond)
    
    return BaseResponse[FishPondResponse](
        code=200,
        msg="创建成功",
        data=FishPondResponse(**new_pond)
    )


@router.put("/update/{pond_id}", response_model=BaseResponse[FishPondResponse])
def update_pond(pond_id: str, data: FishPondUpdate):
    """更新鱼塘"""
    pond = next((p for p in mock_ponds if p["id"] == pond_id), None)
    if not pond:
        raise HTTPException(status_code=404, detail="鱼塘不存在")
    
    if data.name:
        pond["name"] = data.name
    if data.code:
        pond["code"] = data.code
    if data.volume:
        pond["volume"] = data.volume
    if data.fish_type:
        pond["fish_type"] = data.fish_type
    if data.fish_count:
        pond["fish_count"] = data.fish_count
    if data.status:
        pond["status"] = data.status
    if data.remark:
        pond["remark"] = data.remark
    
    pond["update_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return BaseResponse[FishPondResponse](
        code=200,
        msg="更新成功",
        data=FishPondResponse(**pond)
    )


@router.delete("/delete/{pond_id}", response_model=BaseResponse[dict])
def delete_pond(pond_id: str):
    """删除鱼塘"""
    global mock_ponds
    pond = next((p for p in mock_ponds if p["id"] == pond_id), None)
    if not pond:
        raise HTTPException(status_code=404, detail="鱼塘不存在")
    
    mock_ponds = [p for p in mock_ponds if p["id"] != pond_id]
    
    return BaseResponse[dict](
        code=200,
        msg="删除成功",
        data={"id": pond_id}
    )
