from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "engine-python"
    app_mode: str = "standalone"
    database_url: str = "postgresql+psycopg://postgres:postgres@postgres:5432/kce"
    redis_url: str = "redis://redis:6379/0"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
