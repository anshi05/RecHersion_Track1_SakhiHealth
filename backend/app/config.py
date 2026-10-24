"""Settings loaded from environment (backend/.env)."""
import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "http://localhost:3000")
    return [o.strip() for o in raw.split(",") if o.strip()]


@dataclass(frozen=True)
class Settings:
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    anthropic_model: str = field(default_factory=lambda: os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5"))
    llm_timeout_s: float = field(default_factory=lambda: float(os.getenv("LLM_TIMEOUT_S", "8")))
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./sakhi.db"))
    cors_origins: list[str] = field(default_factory=_origins)
    reports_dir: str = field(default_factory=lambda: os.getenv("REPORTS_DIR", "./reports"))

    @property
    def llm_live(self) -> bool:
        return bool(self.anthropic_api_key.strip())


def get_settings() -> Settings:
    return Settings()
