from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./data/smart_fishery_db.db"

    ai_mode: str = "real"
    agent_sk: str = ""
    ai_model: str = "qwen3.5-flash"
    ai_base_url: str = ""

    GROWTH_SMALL_THRESHOLD: float = 15.0
    GROWTH_LARGE_THRESHOLD: float = 25.0

    # 生长识别推理路径开关：legacy（旧双类 YOLO，回退）| two_stage（冻结两阶段管线）
    # 2026-08-08 用户授权：默认切换 two_stage，legacy 保留作回退。
    GROWTH_PIPELINE: str = "two_stage"
    # 新管线 model manifest 路径（为空时使用正式清单 growth_final.json；
    # 显式指定 growth_candidate.example.json 可用于候选 smoke/回归）
    GROWTH_MANIFEST_PATH: str = ""
    # 新管线推理设备（cpu/cuda:0；训练 Agent 占用 GPU 时使用 cpu）
    GROWTH_PIPELINE_DEVICE: str = "cpu"
    # 视频模式时序 override：None=跟随 manifest（正式清单启用 S1）；
    # True/False 可强制开启/关闭（实验用途）。
    GROWTH_VIDEO_TEMPORAL_ENABLED: Optional[bool] = None

    # 视频文件扫描目录（相对 backend 目录）
    VIDEO_DIR: str = "../frontend/public/video"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
