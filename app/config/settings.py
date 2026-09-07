from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, loaded from environment variables / .env.

    Only secrets are supposed to live in the environment — nothing here is
    hardcoded to a real token or API key.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Telegram
    telegram_bot_token: str = ""
    admin_telegram_user_id: int | None = None

    # Database
    database_url: str = "sqlite+aiosqlite:///./ai_news_radar.db"

    # LLM
    llm_provider: str = "mock"
    llm_api_key: str = ""
    llm_model: str = "gemini-2.0-flash"
    llm_api_base: str = ""

    # Timezone / schedule
    timezone: str = "Asia/Almaty"
    digest_hour: int = 8
    digest_minute: int = 0
    collection_interval_minutes: int = 180

    # Logging
    log_level: str = "INFO"

    @property
    def is_configured_for_telegram(self) -> bool:
        return bool(self.telegram_bot_token)


@lru_cache
def get_settings() -> Settings:
    return Settings()
