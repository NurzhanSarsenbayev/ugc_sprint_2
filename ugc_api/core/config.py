# ugc_api/core/config.py
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "engagement_service"
    env: str = Field(default="local")
    host: str = "0.0.0.0"
    port: int = 8080

    mongo_dsn: str = "mongodb://mongo:27017/?replicaSet=rs0"
    mongo_db: str = "engagement"

    sentry_dsn: str = ""

    # Pydantic v2: модель конфигурации
    model_config = SettingsConfigDict(env_file="infra/.env", extra="ignore")


settings = Settings()
