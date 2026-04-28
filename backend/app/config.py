"""Runtime configuration loaded from environment variables."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv(override=True)


@dataclass(frozen=True)
class Settings:
    anthropic_api_key: str
    anthropic_model: str
    allowed_origins: list[str]
    max_upload_bytes: int
    api_secret: str            # optional; if set, X-API-Key header is required
    rate_limit_per_minute: int # 0 = disabled
    max_question_length: int
    max_history_turns: int     # user+assistant pairs to keep


def _split_csv(raw: str) -> list[str]:
    return [s.strip() for s in raw.split(",") if s.strip()]


def get_settings() -> Settings:
    return Settings(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", "").strip(),
        anthropic_model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5"),
        allowed_origins=_split_csv(os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")),
        max_upload_bytes=int(os.getenv("MAX_UPLOAD_BYTES", str(25 * 1024 * 1024))),
        api_secret=os.getenv("API_SECRET", "").strip(),
        rate_limit_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "30")),
        max_question_length=int(os.getenv("MAX_QUESTION_LENGTH", "2000")),
        max_history_turns=int(os.getenv("MAX_HISTORY_TURNS", "10")),
    )


settings = get_settings()
