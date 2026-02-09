# ugc_api/core/config.py
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "engagement_service"
    env: str = Field(default="local")
    host: str = "0.0.0.0"
    port: int = 8080

    mongo_dsn: str = Field(
        default="mongodb://mongo:27017/engagement?replicaSet=rs0", alias="MONGO_DSN"
    )
    mongo_db: str = "engagement"

    redis_dsn: str = Field(default="redis://redis:6379/0", alias="REDIS_DSN")
    film_stats_cache_ttl: int = Field(default=60, alias="FILM_STATS_CACHE_TTL")

    sentry_dsn: str = Field(default="", alias="SENTRY_DSN")
    sentry_test_enabled: bool = Field(default=False, alias="SENTRY_TEST_ENABLED")
    # Pydantic v2
    model_config = SettingsConfigDict(env_file="infra/.env", extra="ignore")


settings = Settings()
