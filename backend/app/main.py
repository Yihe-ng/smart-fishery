from fastapi import FastAPI
from contextlib import asynccontextmanager
from datetime import datetime
from app.api.v1.api import api_router
from app.websocket.routes import ws_router
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    print("应用启动中...")
    print("应用启动完成")
    
    yield
    
    # 关闭时执行
    print("应用关闭中...")
    print("应用已关闭")


app = FastAPI(
    title="石斑鱼养殖水质检测系统",
    description="智能渔业管理系统API文档",
    version="1.0.0",
    lifespan=lifespan
)

# 实现跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3006",      # Vite 本地地址
        "http://127.0.0.1:3006",
        "http://localhost:3008",      # 备用端口
        "http://127.0.0.1:3008",
    ],
    allow_credentials=True,           # 允许携带 Cookie
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含 API 路由
app.include_router(api_router, prefix="/api")

# 包含 WebSocket 路由
app.include_router(ws_router)


@app.get("/")
async def root_route():
    """首页接口"""
    return {
        "status": "success",
        "message": "欢迎来到石斑鱼养殖水质检测系统,后端接口已成功运行",
        "features": [
            "异步数据库操作",
            "WebSocket 实时通信",
            "后台任务调度",
            "智能投喂决策"
        ]
    }


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    from datetime import datetime
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
