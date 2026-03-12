from fastapi import FastAPI
from app.api.v1.api import api_router
from fastapi.middleware.cors import CORSMiddleware
from db.session import engine
from db.base import Base

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="石斑鱼养殖水质检测系统",
    description="智能渔业管理系统API文档",
    version="1.0.0"
)

# 实现跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3006",      # 你的 Vite 本地地址
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

@app.get("/")
def root_route():
    """首页接口"""
    return {
        "status":"success",
        "message":"欢迎来到石斑鱼养殖水质检测系统,后端接口已成功运行"
    }

if __name__=="__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
