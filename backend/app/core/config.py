from pydantic_settings import BaseSettings,SettingsConfigDict

class Settings(BaseSettings):
    POSTGRES_USER:str
    POSTGRES_PASSWARD:str
    POSTGRES_SERVER:str
    POSTGRES_DB:str
    POSTGRES_PORT:int
    SQLALCHEMY_DATABASE_URL:str

model_config=SettingsConfigDict(env_file=".env")
settings=Settings()