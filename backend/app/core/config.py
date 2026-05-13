from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./data/smart_fishery_db.db"

    ai_mode: str = "real"
    agent_sk: str = ""
    ai_model: str = "qwen3.5-flash"
    ai_base_url: str = ""

    GROWTH_SMALL_THRESHOLD: float = 15.0
    GROWTH_LARGE_THRESHOLD: float = 25.0

    # 视频文件扫描目录（相对 backend 目录）
    VIDEO_DIR: str = "../frontend/public/video"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
