from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
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

# 构建数据库连接字符串
DATABASE_URL = f"postgresql://{user}:{encoded_password}@{server}:{port}/{db}"

# 创建数据库引擎
engine = create_engine(DATABASE_URL)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()