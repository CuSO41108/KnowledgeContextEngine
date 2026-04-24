from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "engine-python"
    app_mode: str = "standalone"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
