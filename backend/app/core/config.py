from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./data/smart_fishery_db.db"

    ai_mode: str = "real"
    agent_sk: str = ""
    ai_model: str = "qwen3.5-flash"
    ai_base_url: str = ""

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
