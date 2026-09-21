from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Adaptive Learning API"
    environment: str = "development"
    database_url: str = "sqlite:///./adaptive.db"
    cors_origins: str = "http://localhost:3000"
    llm_provider: str = "fake"
    openai_model: str = "gpt-5.6"
    openai_api_key: str | None = None
    research_provider: str = "curated"
    auth_required: bool = True
    code_runner_image: str = "python:3.13-alpine"
    code_runner_timeout_seconds: int = 5
    code_runner_work_root: str | None = None
    code_runner_in_container: bool = False
    model_config = SettingsConfigDict(
        env_file=("../../../.env.local", ".env.local", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
