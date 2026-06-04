"""Application configuration."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
OPEN_TRADING_API_ROOT = WORKSPACE_ROOT / "open-trading-api"
EXAMPLES_USER_ROOT = OPEN_TRADING_API_ROOT / "examples_user"
DOMESTIC_STOCK_ROOT = EXAMPLES_USER_ROOT / "domestic_stock"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(WORKSPACE_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "local"
    database_url: str = "sqlite:///./data/analyzer.sqlite"
    kis_config_path: str = ""
    kis_svr: str = "prod"  # prod=실전, vps=모의
    news_provider: str = "naver"
    naver_client_id: str = ""
    naver_client_secret: str = ""
    opendart_api_key: str = ""
    llm_provider: str = "openai"
    openai_api_key: str = ""
    google_api_key: str = ""
    llm_model: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    cors_origins: str = "http://localhost:3000"

    @property
    def kis_config_resolved(self) -> Path | None:
        if self.kis_config_path:
            p = Path(self.kis_config_path).expanduser()
            if p.exists():
                return p
        default = Path.home() / "KIS" / "config" / "kis_devlp.yaml"
        return default if default.exists() else None

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def llm_model_resolved(self) -> str:
        if self.llm_model and self.llm_model.strip():
            return self.llm_model.strip()
        if (self.llm_provider or "openai").lower().strip() == "google":
            return "gemini-2.0-flash"
        return "gpt-4o-mini"

    @property
    def database_path_resolved(self) -> Path:
        url = self.database_url
        if url.startswith("sqlite:///"):
            rel = url.replace("sqlite:///", "")
            p = Path(rel)
            if not p.is_absolute():
                return WORKSPACE_ROOT / "app" / "backend" / p
            return p
        return WORKSPACE_ROOT / "app" / "backend" / "data" / "analyzer.sqlite"


@lru_cache
def get_settings() -> Settings:
    return Settings()
