"""WebSocket 连接管理器"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set, List
import json
from datetime import datetime
import asyncio


class ConnectionManager:
    """WebSocket 连接管理器"""
    
    def __init__(self):
        # 存储活跃的 WebSocket 连接 {device_id: WebSocket}
        self.active_connections: Dict[str, WebSocket] = {}
        # 设备状态缓存
        self.device_status: Dict[str, dict] = {}
        # 按类型分组的连接
        self.connections_by_type: Dict[str, Set[str]] = {
            'feeder': set(),      # 投喂设备
            'sensor': set(),      # 传感器
            'camera': set(),      # 摄像头
            'client': set()       # 前端客户端
        }
    
    async def connect(self, websocket: WebSocket, device_id: str, device_type: str = 'client'):
        """建立 WebSocket 连接"""
        await websocket.accept()
        self.active_connections[device_id] = websocket
        self.connections_by_type[device_type].add(device_id)
        self.device_status[device_id] = {
            'device_type': device_type,
            'status': 'online',
            'connected_at': datetime.now().isoformat()
        }
        print(f"[{device_type}] 设备 {device_id} 已连接")
        
        # 广播设备上线消息
        await self.broadcast_message({
            'type': 'device_online',
            'device_id': device_id,
            'device_type': device_type,
            'timestamp': datetime.now().isoformat()
        })
    
    def disconnect(self, device_id: str):
        """断开 WebSocket 连接"""
        if device_id in self.active_connections:
            device_type = self.device_status.get(device_id, {}).get('device_type', 'unknown')
            self.connections_by_type.get(device_type, set()).discard(device_id)
            del self.active_connections[device_id]
            
            if device_id in self.device_status:
                self.device_status[device_id]['status'] = 'offline'
                self.device_status[device_id]['disconnected_at'] = datetime.now().isoformat()
            
            print(f"[{device_type}] 设备 {device_id} 已断开")
    
    async def send_message(self, device_id: str, message: dict):
        """向指定设备发送消息"""
        if device_id in self.active_connections:
            websocket = self.active_connections[device_id]
            await websocket.send_json(message)
            return True
        return False
    
    async def send_command(self, device_id: str, command: str, data: dict = None):
        """向设备发送控制指令"""
        message = {
            'type': 'command',
            'command': command,
            'timestamp': datetime.now().isoformat(),
            'data': data or {}
        }
        success = await self.send_message(device_id, message)
        if not success:
            raise Exception(f"设备 {device_id} 不在线")
        return success
    
    async def broadcast_message(self, message: dict, device_type: str = None):
        """广播消息给所有或指定类型的设备"""
        if device_type:
            target_devices = self.connections_by_type.get(device_type, set())
        else:
            target_devices = set(self.active_connections.keys())
        
        # 并发发送消息
        tasks = []
        for device_id in target_devices:
            if device_id in self.active_connections:
                tasks.append(self.send_message(device_id, message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def broadcast_status(self, device_id: str, status: dict):
        """广播设备状态更新"""
        message = {
            'type': 'status_update',
            'device_id': device_id,
            'timestamp': datetime.now().isoformat(),
            'data': status
        }
        # 广播给所有客户端
        await self.broadcast_message(message, device_type='client')
    
    def get_online_devices(self, device_type: str = None) -> List[str]:
        """获取在线设备列表"""
        if device_type:
            return list(self.connections_by_type.get(device_type, set()))
        return list(self.active_connections.keys())
    
    def get_device_status(self, device_id: str) -> dict:
        """获取设备状态"""
        return self.device_status.get(device_id, {})


# 全局连接管理器实例
manager = ConnectionManager()
