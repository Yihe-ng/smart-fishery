"""WebSocket 路由"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.websocket.manager import manager
import json
from datetime import datetime

ws_router = APIRouter()


@ws_router.websocket("/ws/device/{device_id}")
async def device_websocket(
    websocket: WebSocket,
    device_id: str,
    device_type: str = Query('client', description="设备类型: feeder/sensor/camera/client")
):
    """设备 WebSocket 连接端点"""
    await manager.connect(websocket, device_id, device_type)
    
    try:
        while True:
            # 接收设备消息
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # 处理不同类型的消息
            msg_type = message.get('type')
            
            if msg_type == 'status_report':
                # 设备状态上报
                status_data = message.get('data', {})
                manager.device_status[device_id].update(status_data)
                # 广播给所有客户端
                await manager.broadcast_status(device_id, status_data)
                
            elif msg_type == 'command_response':
                # 设备执行指令后的响应
                await manager.broadcast_message({
                    'type': 'command_response',
                    'device_id': device_id,
                    'timestamp': datetime.now().isoformat(),
                    'data': message.get('data', {})
                }, device_type='client')
                
            elif msg_type == 'sensor_data':
                # 传感器数据上报
                await manager.broadcast_message({
                    'type': 'sensor_data',
                    'device_id': device_id,
                    'timestamp': datetime.now().isoformat(),
                    'data': message.get('data', {})
                }, device_type='client')
                
            elif msg_type == 'alert':
                # 告警上报
                await manager.broadcast_message({
                    'type': 'alert',
                    'device_id': device_id,
                    'timestamp': datetime.now().isoformat(),
                    'data': message.get('data', {})
                })
                
    except WebSocketDisconnect:
        manager.disconnect(device_id)
        # 广播设备离线消息
        await manager.broadcast_message({
            'type': 'device_offline',
            'device_id': device_id,
            'timestamp': datetime.now().isoformat()
        })


@ws_router.websocket("/ws/feeding/{feeder_id}")
async def feeding_websocket(
    websocket: WebSocket,
    feeder_id: str
):
    """投喂设备专用 WebSocket 端点"""
    await manager.connect(websocket, feeder_id, 'feeder')
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get('type') == 'feeding_status':
                # 投喂状态更新
                await manager.broadcast_message({
                    'type': 'feeding_status',
                    'feeder_id': feeder_id,
                    'timestamp': datetime.now().isoformat(),
                    'data': message.get('data', {})
                }, device_type='client')
                
            elif message.get('type') == 'feeding_complete':
                # 投喂完成
                await manager.broadcast_message({
                    'type': 'feeding_complete',
                    'feeder_id': feeder_id,
                    'timestamp': datetime.now().isoformat(),
                    'data': message.get('data', {})
                }, device_type='client')
                
    except WebSocketDisconnect:
        manager.disconnect(feeder_id)


@ws_router.websocket("/ws/camera/{camera_id}")
async def camera_websocket(
    websocket: WebSocket,
    camera_id: str
):
    """摄像头专用 WebSocket 端点（用于实时视频流控制）"""
    await manager.connect(websocket, camera_id, 'camera')
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get('type') == 'detection_result':
                # AI 检测结果
                await manager.broadcast_message({
                    'type': 'detection_result',
                    'camera_id': camera_id,
                    'timestamp': datetime.now().isoformat(),
                    'data': message.get('data', {})
                }, device_type='client')
                
    except WebSocketDisconnect:
        manager.disconnect(camera_id)
