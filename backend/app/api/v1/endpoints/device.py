from fastapi import APIRouter, HTTPException, Query
from app.schemas.base import BaseResponse, PageQuery, PageResult
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter()


class SensorDeviceBase(BaseModel):
    """传感器设备基础模型"""
    device_id: str
    device_name: str
    pond_id: str
    status: str


class SensorDeviceCreate(SensorDeviceBase):
    """创建传感器设备模型"""
    pass


class SensorDeviceResponse(SensorDeviceBase):
    """传感器设备响应模型"""
    id: int
    create_time: str


# 模拟设备数据
mock_devices = [
    {
        "id": "temp-001",
        "name": "水温传感器",
        "type": "temperature",
        "status": "online",
        "lastOnlineTime": datetime.now().isoformat(),
        "lastData": 25.5,
        "unit": "℃",
        "location": "1号池东侧"
    },
    {
        "id": "ph-001",
        "name": "pH传感器",
        "type": "ph",
        "status": "online",
        "lastOnlineTime": datetime.now().isoformat(),
        "lastData": 7.2,
        "unit": "",
        "location": "1号池中心"
    },
    {
        "id": "do-001",
        "name": "溶氧传感器",
        "type": "dissolved_oxygen",
        "status": "online",
        "lastOnlineTime": datetime.now().isoformat(),
        "lastData": 6.8,
        "unit": "mg/L",
        "location": "1号池西侧"
    },
    {
        "id": "nh3-001",
        "name": "氨氮传感器",
        "type": "ammonia_nitrogen",
        "status": "online",
        "lastOnlineTime": datetime.now().isoformat(),
        "lastData": 0.3,
        "unit": "mg/L",
        "location": "总进水口"
    },
    {
        "id": "no2-001",
        "name": "亚硝酸盐传感器",
        "type": "nitrite",
        "status": "offline",
        "lastOnlineTime": datetime.now().isoformat(),
        "lastData": 0.05,
        "unit": "mg/L",
        "location": "总出水口"
    }
]


class DeviceResponse(BaseModel):
    """设备响应模型（前端使用）"""
    id: str
    name: str
    type: str
    status: str
    lastOnlineTime: str
    lastData: float
    unit: str
    location: str


@router.get("/list", response_model=BaseResponse[List[DeviceResponse]])
def get_device_list(
    status: Optional[str] = Query(None, description="状态筛选"),
    pond_id: Optional[str] = Query(None, description="鱼塘ID筛选")
):
    """获取传感器设备列表"""
    filtered_devices = mock_devices.copy()
    
    if status:
        filtered_devices = [d for d in filtered_devices if d["status"] == status]
    
    if pond_id:
        filtered_devices = [d for d in filtered_devices if d["location"] and pond_id in d["location"]]
    
    return BaseResponse[List[DeviceResponse]](
        code=200,
        msg="获取成功",
        data=[DeviceResponse(**device) for device in filtered_devices]
    )


@router.get("/{device_id}", response_model=BaseResponse[DeviceResponse])
def get_device_detail(device_id: str):
    """获取设备详情"""
    device = next((d for d in mock_devices if d["id"] == device_id), None)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    return BaseResponse[DeviceResponse](
        code=200,
        msg="获取成功",
        data=DeviceResponse(**device)
    )
