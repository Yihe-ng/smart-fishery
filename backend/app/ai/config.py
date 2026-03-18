from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"


class AISettings(BaseSettings):
    agent_sk: Optional[str] = None
    ai_mode: Literal["mock", "real"] = "mock"
    ai_model: str = "qwen3.5-flash"
    ai_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        extra="ignore",
        env_prefix="",
    )


@lru_cache(maxsize=1)
def get_ai_settings() -> AISettings:
    return AISettings()
