"""App settings, read from environment variables and the repo-root .env file."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")

    database_url: str = "postgresql://lamp:lamp@localhost:5432/lamp"
    registry_key: str = "dev-registry-key-change-me"
    llm_mode: str = "replay"
    openai_api_key: str = ""
    openai_extract_model: str = "gpt-6-luna"
    llm_daily_budget_usd: float = 1.00
    cors_origins: list[str] = ["http://localhost:3000"]


settings = Settings()
