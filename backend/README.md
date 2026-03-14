# 石斑鱼养殖水质检测系统 - 后端文档

## 项目概述

基于 FastAPI 开发的智能渔业管理系统后端，提供水质监测、智能投喂、设备管理、病害检测等核心功能。

## 技术栈

- **框架**: FastAPI 0.100+
- **数据库**: PostgreSQL 14+
- **ORM**: SQLAlchemy 2.0 (异步支持)
- **驱动**: asyncpg (异步 PostgreSQL 驱动)
- **任务调度**: APScheduler (异步调度)
- **WebSocket**: 原生 FastAPI WebSocket
- **Python**: 3.9+

## 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # 应用入口
│   ├── api/
│   │   └── v1/
│   │       ├── api.py            # 路由聚合
│   │       └── endpoints/        # API 端点
│   │           ├── auth.py       # 认证模块
│   │           ├── water_quality.py  # 水质检测
│   │           ├── fish_pond.py      # 鱼塘管理
│   │           ├── feeding.py        # 投喂管理
│   │           ├── device.py         # 设备管理
│   │           ├── alert.py          # 告警管理
│   │           ├── health.py         # 健康总览
│   │           ├── disease.py        # 病害检测
│   │           ├── user.py           # 用户管理
│   │           ├── role.py           # 角色管理
│   │           └── menu.py           # 菜单管理
│   ├── core/
│   │   └── config.py             # 配置管理
│   ├── db/
│   │   ├── base.py               # 模型基类
│   │   ├── session.py            # 同步会话
│   │   └── async_session.py      # 异步会话
│   ├── models/
│   │   ├── water.py              # 水质模型
│   │   └── user.py               # 用户模型
│   ├── schemas/
│   │   ├── base.py               # 基础 Schema
│   │   ├── water.py              # 水质 Schema
│   │   └── user.py               # 用户 Schema
│   ├── crud/
│   │   ├── crud_water.py         # 同步 CRUD
│   │   └── crud_water_async.py   # 异步 CRUD
│   ├── services/
│   │   ├── water_analysis.py     # 水质分析服务
│   │   └── smart_feeding.py      # 智能投喂服务
│   ├── websocket/
│   │   ├── manager.py            # WebSocket 管理器
│   │   └── routes.py             # WebSocket 路由
│   └── tasks/
│       └── scheduler.py          # 任务调度器
├── algorithms/
│   └── prediction.py             # 水质预测算法
├── tests/                        # 测试目录
├── .env                          # 环境变量
├── requirements.txt              # 依赖列表
└── README.md                     # 本文档
```

## 核心功能模块

### 1. 水质检测模块 (water_quality)

#### 功能说明
- 接收传感器水质数据
- 实时水质分析与预警
- 历史数据查询
- 阈值配置管理

#### API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/water-quality/data` | POST | 接收水质数据 |
| `/api/water-quality/latest` | GET | 获取最新数据 |
| `/api/water-quality/history` | POST | 获取历史数据 |
| `/api/water-quality/threshold` | GET | 获取阈值配置 |

#### 数据模型

```python
class WaterQualityData:
    - sensor_id: str          # 传感器ID
    - pond_id: str            # 鱼塘ID
    - dissolved_oxygen: float # 溶解氧 mg/L
    - ph_value: float         # pH值
    - temperature: float      # 温度 ℃
    - ammonia_nitrogen: float # 氨氮 mg/L
    - nitrite: float          # 亚硝酸盐 mg/L
    - analysis_result: str    # 分析结果
    - alert_level: str        # 预警级别
    - created_at: datetime    # 创建时间
```

#### 预警规则

| 参数 | 正常范围 | 预警阈值 | 危险阈值 |
|------|----------|----------|----------|
| 溶解氧 | 5-15 mg/L | < 5 mg/L | < 3 mg/L |
| 温度 | 22-28 ℃ | < 20 或 > 30 ℃ | < 15 或 > 35 ℃ |
| pH值 | 6.5-8.5 | < 6.5 或 > 8.5 | < 6 或 > 9 |
| 氨氮 | < 0.5 mg/L | > 0.5 mg/L | > 1.0 mg/L |
| 亚硝酸盐 | < 0.1 mg/L | > 0.1 mg/L | > 0.2 mg/L |

### 2. 智能投喂模块 (feeding)

#### 功能说明
- 基于水质的智能投喂决策
- 多因子综合评估算法
- WebSocket 实时设备控制
- 投喂日志记录

#### 智能决策算法

```
投喂量 = 基础投喂量 × 溶解氧因子 × 温度因子 × pH因子 × 氨氮因子 × 亚硝酸盐因子

基础投喂量 = 鱼总重量 × 2.5%
鱼总重量 = 鱼数量 × 平均鱼重
```

#### 调整因子说明

| 因子 | 正常值 | 调整规则 |
|------|--------|----------|
| 溶解氧因子 | 1.0 | <3→0.3, <5→0.6, >8→1.2 |
| 温度因子 | 1.0 | 极端→0.2, 偏离→0.5-0.9 |
| pH因子 | 1.0 | 异常→0.7, 偏离→0.85 |
| 氨氮因子 | 1.0 | >0.5→0.7, >0.3→0.85 |
| 亚硝酸盐因子 | 1.0 | >0.1→0.8, >0.05→0.9 |

#### API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/feeding/config` | GET/POST | 投喂配置管理 |
| `/api/feeding/logs` | GET | 投喂日志查询 |
| `/api/feeding/manual` | POST | 手动投喂 |
| `/api/feeding/smart` | POST | 智能投喂决策 |
| `/api/feeding/execute` | POST | 执行投喂指令 |
| `/api/feeding/devices/online` | GET | 在线设备列表 |
| `/api/feeding/devices/{id}/status` | GET | 设备状态查询 |

#### WebSocket 接口

```
ws://localhost:8000/ws/feeding/{feeder_id}

消息类型:
- feeding_status: 投喂状态更新
- feeding_complete: 投喂完成通知
- command: 控制指令
```

### 3. 鱼塘管理模块 (fish_pond)

#### 功能说明
- 鱼塘 CRUD 操作
- 鱼塘状态管理
- 养殖信息维护

#### API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/fish-pond/list` | GET | 获取鱼塘列表 |
| `/api/fish-pond/detail/{id}` | GET | 获取鱼塘详情 |
| `/api/fish-pond/create` | POST | 创建鱼塘 |
| `/api/fish-pond/update` | PUT | 更新鱼塘 |
| `/api/fish-pond/delete/{id}` | DELETE | 删除鱼塘 |

#### 鱼塘状态

- `running`: 正常运行
- `stopped`: 暂停养殖
- `maintenance`: 维护中

### 4. 设备管理模块 (device)

#### 功能说明
- 传感器设备管理
- 设备状态监控
- 在线/离线检测

#### 支持的设备类型

- `temperature`: 水温传感器
- `ph`: pH传感器
- `dissolved_oxygen`: 溶氧传感器
- `ammonia_nitrogen`: 氨氮传感器
- `nitrite`: 亚硝酸盐传感器
- `camera`: 摄像头
- `feeder`: 投喂机

#### API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/device/list` | GET | 获取设备列表 |
| `/api/device/{id}` | GET | 获取设备详情 |

### 5. 告警管理模块 (alert)

#### 功能说明
- 实时告警监控
- 告警历史查询
- 告警确认/处理

#### 告警类型

- `water_quality`: 水质异常
- `device_offline`: 设备离线
- `disease_detected`: 病害检测

#### 告警级别

- `critical`: 严重（红色）
- `warning`: 警告（黄色）
- `info`: 提示（蓝色）

#### API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/alert/recent` | GET | 获取最近告警 |
| `/api/alert/list` | GET | 告警列表查询 |
| `/api/alert/{id}/resolve` | POST | 确认/忽略告警 |

### 6. 病害检测模块 (disease)

#### 功能说明
- AI 病害识别
- 实时视频流
- 检测结果记录

#### 支持病害类型

- `gill_rot`: 烂鳃病
- `red_skin`: 赤皮病
- `enteritis`: 肠炎
- `healthy`: 健康

#### API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/disease/detect` | POST | 病害检测（图片） |
| `/api/disease/camera/stream` | GET | 获取视频流地址 |

### 7. 健康总览模块 (health)

#### 功能说明
- 养殖健康评分
- 病害风险评估
- 综合状态展示

#### API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/health/overview` | GET | 获取健康总览 |

#### 健康评分算法

```
健康评分 = 100 - (水质扣分 + 病害扣分 + 设备扣分)

水质扣分: 根据各指标偏离程度计算
病害扣分: 根据检测到的病害数量和严重程度
设备扣分: 根据离线设备数量和重要性
```

### 8. 系统管理模块

#### 用户管理 (user)

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/user/list` | GET | 用户列表 |
| `/api/user` | POST/PUT/DELETE | 用户CRUD |

#### 角色管理 (role)

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/role/list` | GET | 角色列表 |

#### 菜单管理 (menu)

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v3/system/menus/simple` | GET | 菜单列表 |

#### 认证 (auth)

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/auth/login` | POST | 用户登录 |
| `/api/auth/user/info` | GET | 获取用户信息 |

## WebSocket 实时通信

### 连接管理

```python
# WebSocket 管理器功能
- 设备连接管理
- 消息广播
- 状态同步
- 指令下发
```

### WebSocket 端点

```
# 通用设备连接
ws://localhost:8000/ws/device/{device_id}?device_type={type}

# 投喂设备专用
ws://localhost:8000/ws/feeding/{feeder_id}

# 摄像头专用
ws://localhost:8000/ws/camera/{camera_id}
```

### 消息格式

```json
// 设备状态上报
{
  "type": "status_report",
  "data": {
    "status": "online",
    "battery": 85,
    "signal": 90
  }
}

// 控制指令
{
  "type": "command",
  "command": "feed",
  "data": {
    "amount": 500,
    "duration": 30
  }
}

// 指令响应
{
  "type": "command_response",
  "data": {
    "success": true,
    "message": "投喂完成"
  }
}
```

## 后台任务调度

### 定时任务列表

| 任务名称 | 执行频率 | 说明 |
|----------|----------|------|
| water_quality_check | 每5分钟 | 水质告警检查 |
| auto_feeding | 每30分钟 | 自动投喂检查 |
| daily_report | 每天凌晨1点 | 生成日报 |
| cleanup_data | 每周日凌晨3点 | 清理过期数据 |

### 任务配置

```python
# 在 app/tasks/scheduler.py 中配置
scheduler.add_job(
    check_water_quality_alerts,
    trigger=IntervalTrigger(seconds=300),
    id='water_quality_check'
)
```

## 异步架构

### 异步数据库操作

```python
# 使用 asyncpg 驱动
from sqlalchemy.ext.asyncio import AsyncSession

async def get_data(db: AsyncSession):
    result = await db.execute(query)
    return result.scalars().all()
```

### 异步 API 端点

```python
@router.get("/data")
async def get_data(db: AsyncSession = Depends(get_async_db)):
    data = await crud.get_data(db)
    return data
```

### 性能优势

- 支持高并发请求
- 非阻塞 I/O 操作
- 数据库连接池管理
- 更好的资源利用率

## 环境配置

### 环境变量

```env
# 数据库配置
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_DB=smart_fish_db

# 应用配置
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 安装依赖

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt
```

### 启动服务

```bash
# 开发模式（热重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API 文档

启动服务后访问：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## 测试

```bash
# 运行测试
pytest tests/

# 覆盖率测试
pytest --cov=app tests/
```

## 部署建议

### 生产环境配置

1. **使用 Gunicorn + Uvicorn**
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

2. **使用 Nginx 反向代理**
```nginx
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

3. **Docker 部署**
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 开发规范

### 代码风格

- 遵循 PEP 8 规范
- 使用类型注解
- 编写文档字符串
- 异步函数使用 async/await

### 提交规范

```
feat: 新功能
fix: 修复bug
docs: 文档更新
style: 代码格式调整
refactor: 重构代码
test: 测试相关
chore: 构建/工具相关
```

## 联系方式

如有问题，请联系开发团队。

---

**最后更新**: 2024年
