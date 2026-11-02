"""Runtime configuration (12-factor: everything comes from the environment)."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False)

    app_name: str = "jobs-api"
    app_version: str = "1.0.0"
    environment: str = "local"
    log_level: str = "INFO"

    database_url: str = "sqlite:///./jobs.db"
    redis_url: str = "redis://localhost:6379/0"
    queue_name: str = "jobs:queue"

    # Optional HashiCorp Vault integration. When VAULT_ADDR is set the DB password
    # is read from Vault KV v2 instead of being passed in plain env vars.
    vault_addr: str | None = None
    vault_token: str | None = None
    vault_secret_path: str = "jobs-platform/database"


@lru_cache
def get_settings() -> Settings:
    return Settings()
