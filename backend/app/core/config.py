from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """全局环境配置（由 backend/.env 覆盖默认值）。

    ⚠️ 配置分工说明（三层，互不重叠）：
    - 本文件只放"运行开关/入口"：选哪个管线、用哪个配置文件、推理设备、目录。
    - 模型清单 `config/growth/pipeline.final.json` 管"怎么测"：模型与权重、裁剪、
      视频时序、测长算法与几何质量门槛、像素→厘米换算、可测性准入策略。
    - 养殖标准 `config/growth/grouper_growth_standard.json` 管"测出来怎么评"：
      第 3–15 个月预期累计增长量、每月偏小/偏大比例、群体最小样本与去极端规则、
      视频最少可评价帧数和体长估重公式。
    - 已删除的历史死配置：GROWTH_SMALL_THRESHOLD / GROWTH_LARGE_THRESHOLD；
      体长分档与估重曾在 manifest.business 段，现已迁至养殖标准 JSON。
    """

    DATABASE_URL: str = "sqlite:///./data/smart_fishery_db.db"

    ai_mode: str = "real"
    agent_sk: str = ""
    ai_model: str = "qwen3.5-flash"
    ai_base_url: str = ""

    # 生长识别推理路径开关：legacy（旧双类 YOLO，回退）| two_stage（冻结两阶段管线）
    # 2026-08-08 用户授权：默认切换 two_stage，legacy 保留作回退。
    GROWTH_PIPELINE: str = "two_stage"
    # 新管线模型清单路径（为空时使用 config/growth/pipeline.final.json；
    # 显式指定 config/growth/pipeline.candidate.example.json 可用于候选 smoke/回归）
    GROWTH_MANIFEST_PATH: str = ""
    # 养殖标准（月度生长评价规则）路径；为空时使用
    # config/growth/grouper_growth_standard.json。修改 JSON 后需重启后端生效。
    GROWTH_STANDARD_PATH: str = ""
    # 新管线推理设备（cpu/cuda:0；训练 Agent 占用 GPU 时使用 cpu）
    GROWTH_PIPELINE_DEVICE: str = "cpu"
    # 视频模式时序 override：None=跟随 manifest（正式清单启用 S1）；
    # True/False 可强制开启/关闭（实验用途）。
    GROWTH_VIDEO_TEMPORAL_ENABLED: Optional[bool] = None

    # 视频任务运行参数：只控制采样、任务生命周期和展示资源，不属于养殖评价标准。
    VIDEO_MIN_DURATION_SECONDS: float = 3.0
    VIDEO_TARGET_INTERVAL_SECONDS: float = 2.0
    VIDEO_MIN_FRAMES: int = 3
    VIDEO_MAX_FRAMES: int = 8
    VIDEO_PROCESS_SOFT_LIMIT_SECONDS: float = 120.0
    VIDEO_PROCESS_MAX_SECONDS: float = 180.0
    VIDEO_TASK_TTL_SECONDS: int = 60 * 60
    VIDEO_MAX_TERMINAL_TASKS: int = 3
    VIDEO_DISPLAY_MAX_EDGE: int = 1280
    VIDEO_DISPLAY_JPEG_QUALITY: int = 85

    # 视频文件扫描目录（相对 backend 目录）
    VIDEO_DIR: str = "../frontend/public/video"

    # 统一存储层（app/services/storage.py）：local = 本地文件系统（默认）；
    # object = S3 兼容对象存储（如 MinIO），需同时配置 STORAGE_ENDPOINT / STORAGE_BUCKET
    # 与访问凭据。凭据只从环境变量 / backend/.env 读取，禁止硬编码进仓库。
    STORAGE_BACKEND: str = "local"
    STORAGE_LOCAL_DIR: str = "data/storage"
    STORAGE_ENDPOINT: str = ""
    STORAGE_BUCKET: str = ""
    STORAGE_ACCESS_KEY: str = ""
    STORAGE_SECRET_KEY: str = ""
    STORAGE_SECURE: bool = False

    # 数据保留策略：超期对象由 app/services/retention.py 的 enforce_retention 清理。
    # 天数 <=0 表示该前缀不启用保留清理。默认 raw/（原始图像/视频）留 7 天，
    # results/（识别结果）留 90 天，archive/（归档）留 365 天。
    STORAGE_RAW_RETENTION_DAYS: int = 7
    STORAGE_RESULTS_RETENTION_DAYS: int = 90
    STORAGE_ARCHIVE_RETENTION_DAYS: int = 365

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
