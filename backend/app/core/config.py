from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """全局环境配置（由 backend/.env 覆盖默认值）。

    ⚠️ 配置分工说明：
    - 本文件只放"运行开关/入口"（选哪个管线、用哪个 manifest、设备、目录等）。
    - 算法参数（阈值/换算/分档/估重/准入策略）一律在
      `app/models/ai/pipeline/manifests/growth_final.json`（manifest）中配置，
      不要在 config.py 重复定义——manifest 是这些参数的唯一真源。
    - 已删除的历史死配置：GROWTH_SMALL_THRESHOLD / GROWTH_LARGE_THRESHOLD
      （体长分档实际由 manifest.business.small/large_threshold_cm 控制）。
    """

    DATABASE_URL: str = "sqlite:///./data/smart_fishery_db.db"

    ai_mode: str = "real"
    agent_sk: str = ""
    ai_model: str = "qwen3.5-flash"
    ai_base_url: str = ""

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
