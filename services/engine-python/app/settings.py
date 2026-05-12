from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "engine-python"
    app_mode: str = "standalone"
    database_url: str = "postgresql+psycopg://postgres:postgres@postgres:5432/kce"
    redis_url: str = "redis://redis:6379/0"
    openai_base_url: str = ""
    openai_api_key: str = ""
    openai_chat_model: str = "qwen-plus"
    answer_llm_enabled: bool = False
    answer_llm_timeout_seconds: float = 20.0
    answer_max_tokens: int = 700
    answer_context_max_chars: int = 6000

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
