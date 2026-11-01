from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    api_port: int = Field(default=8000, alias="API_PORT")
    frontend_port: int = Field(default=3000, alias="FRONTEND_PORT")
    database_url: str = Field(default="sqlite:///data/sqlite/satisfactory.db", alias="DATABASE_URL")
    expose_tracebacks: bool = Field(default=True, alias="EXPOSE_TRACEBACKS")

    @property
    def repo_root(self) -> Path:
        return Path(__file__).resolve().parents[4]

    @property
    def static_root(self) -> Path:
        return self.repo_root / "static"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
