from fastapi import APIRouter
from app.schemas.base import BaseResponse
from pydantic import BaseModel
from typing import List
from datetime import datetime, timedelta
import random

router = APIRouter()


class GrowthTrendPoint(BaseModel):
    """生长趋势数据点"""
    date: str
    weight: float  # 平均体重 (g)
    count: int     # 鱼的数量
    feed: float    # 投喂量 (g)


class GrowthTrendResponse(BaseModel):
    """生长趋势响应"""
    data: List[GrowthTrendPoint]


class SizeDistributionPoint(BaseModel):
    """规格分布数据点"""
    size_range: str  # 规格范围
    percentage: float  # 百分比
    count: int  # 数量


class SizeDistributionResponse(BaseModel):
    """规格分布响应"""
    data: List[SizeDistributionPoint]


class FCRRecord(BaseModel):
    """FCR 记录"""
    date: str
    fish_weight: float  # 平均体重 (g)
    feed_total: float   # 累计投喂 (kg)
    fcr: float          # 饲料转化率


class FCRResponse(BaseModel):
    """FCR 响应"""
    data: List[FCRRecord]


class InventoryRecord(BaseModel):
    """盘点记录"""
    timestamp: str
    type: str
    stock: int      # 存栏数量
    average_weight: float  # 平均体重 (g)


class InventoryResponse(BaseModel):
    """盘点记录响应"""
    data: List[InventoryRecord]


@router.get("/trend", response_model=BaseResponse[GrowthTrendResponse])
async def get_growth_trend():
    """获取生长趋势数据"""
    # 生成模拟数据
    data = []
    base_weight = 100  # 初始体重
    base_count = 12000  # 初始数量
    base_feed = 500     # 初始投喂量
    
    for i in range(30):
        date = (datetime.now() - timedelta(days=29 - i)).strftime("%Y-%m-%d")
        # 体重增长：每天增长 5-8g
        weight = base_weight + i * random.uniform(5, 8)
        # 数量减少：每天减少 0-2 尾
        count = base_count - i * random.randint(0, 2)
        # 投喂量增加：每天增加 20-30g
        feed = base_feed + i * random.uniform(20, 30)
        
        data.append(GrowthTrendPoint(
            date=date,
            weight=round(weight, 2),
            count=count,
            feed=round(feed, 2)
        ))
    
    return BaseResponse[GrowthTrendResponse](
        code=200,
        msg="获取成功",
        data=GrowthTrendResponse(data=data)
    )


@router.get("/size-distribution", response_model=BaseResponse[SizeDistributionResponse])
async def get_size_distribution():
    """获取规格分布数据"""
    # 模拟规格分布数据
    data = [
        SizeDistributionPoint(size_range="300-350g", percentage=15.0, count=1875),
        SizeDistributionPoint(size_range="350-400g", percentage=25.0, count=3125),
        SizeDistributionPoint(size_range="400-450g", percentage=35.0, count=4375),
        SizeDistributionPoint(size_range="450-500g", percentage=20.0, count=2500),
        SizeDistributionPoint(size_range="500g以上", percentage=5.0, count=625)
    ]
    
    return BaseResponse[SizeDistributionResponse](
        code=200,
        msg="获取成功",
        data=SizeDistributionResponse(data=data)
    )


@router.get("/fcr", response_model=BaseResponse[FCRResponse])
async def get_fcr_records():
    """获取 FCR 记录"""
    # 模拟 FCR 数据
    data = [
        FCRRecord(date="2024-03-20", fish_weight=450, feed_total=125.5, fcr=1.55),
        FCRRecord(date="2024-03-13", fish_weight=435, feed_total=118.2, fcr=1.58),
        FCRRecord(date="2024-03-06", fish_weight=420, feed_total=112.4, fcr=1.62),
        FCRRecord(date="2024-02-28", fish_weight=405, feed_total=106.8, fcr=1.65),
        FCRRecord(date="2024-02-21", fish_weight=390, feed_total=101.5, fcr=1.68),
        FCRRecord(date="2024-02-14", fish_weight=375, feed_total=96.3, fcr=1.72),
        FCRRecord(date="2024-02-07", fish_weight=360, feed_total=91.2, fcr=1.75)
    ]
    
    return BaseResponse[FCRResponse](
        code=200,
        msg="获取成功",
        data=FCRResponse(data=data)
    )


@router.get("/inventory", response_model=BaseResponse[InventoryResponse])
async def get_inventory_records():
    """获取盘点记录"""
    # 模拟盘点记录
    data = [
        InventoryRecord(
            timestamp="2024-03-15",
            type="常规盘点",
            stock=12500,
            average_weight=450
        ),
        InventoryRecord(
            timestamp="2024-02-15",
            type="常规盘点",
            stock=12550,
            average_weight=380
        ),
        InventoryRecord(
            timestamp="2024-01-15",
            type="常规盘点",
            stock=12600,
            average_weight=310
        ),
        InventoryRecord(
            timestamp="2023-12-15",
            type="常规盘点",
            stock=12650,
            average_weight=240
        ),
        InventoryRecord(
            timestamp="2023-11-15",
            type="常规盘点",
            stock=12700,
            average_weight=170
        )
    ]
    
    return BaseResponse[InventoryResponse](
        code=200,
        msg="获取成功",
        data=InventoryResponse(data=data)
    )
