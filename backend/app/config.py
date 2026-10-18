"""App settings, read from environment variables and the repo-root .env file."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")

    database_url: str = "postgresql://lamp:lamp@localhost:5432/lamp"
    # Secret for the duplicate-financing registry. Required unless DEV_MODE is on.
    registry_key: str = ""
    # Demo controls (/dev/reset, the supplier-reply simulator) exist only when this is true.
    dev_mode: bool = False
    llm_mode: str = "replay"
    openai_api_key: str = ""
    openai_extract_model: str = "gpt-6-luna"
    llm_daily_budget_usd: float = 1.00
    cors_origins: list[str] = ["http://localhost:3000"]


DEV_REGISTRY_KEY = "dev-only-registry-key"
PLACEHOLDER_KEYS = {"", "change-me", "dev-registry-key-change-me"}


def registry_secret() -> str:
    """The registry HMAC key. Outside DEV_MODE a real key must be configured."""
    if settings.registry_key not in PLACEHOLDER_KEYS:
        return settings.registry_key
    if settings.dev_mode:
        return DEV_REGISTRY_KEY
    raise RuntimeError("REGISTRY_KEY is not set. Set it in .env (any long random string), or run with DEV_MODE=true.")


settings = Settings()
