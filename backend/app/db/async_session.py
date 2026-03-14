"""异步数据库会话配置"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

# 加载环境变量
load_dotenv()

# 从环境变量获取数据库配置
user = os.getenv("POSTGRES_USER", "postgres")
password = os.getenv("POSTGRES_PASSWORD", "")
server = os.getenv("POSTGRES_SERVER", "localhost")
port = os.getenv("POSTGRES_PORT", "5432")
db = os.getenv("POSTGRES_DB", "smart_fish_db")

# URL 编码密码（处理特殊字符）
encoded_password = quote_plus(password)

# 构建异步数据库连接字符串（使用 asyncpg 驱动）
DATABASE_URL = f"postgresql+asyncpg://{user}:{encoded_password}@{server}:{port}/{db}"

# 创建异步数据库引擎
async_engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # 生产环境设为 False
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def get_async_db():
    """获取异步数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
