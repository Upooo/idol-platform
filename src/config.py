"""IDOL Platform — Centralized Configuration.

All configuration flows through this single module.
Every other module imports `from src.config import settings`.
No os.getenv() calls anywhere else in the codebase.
"""

from __future__ import annotations

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────
    app_name: str = "IDOL"
    app_env: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    timezone: str = "Asia/Jakarta"

    # ── Telegram: HQ Bot ─────────────────────────────────
    hq_bot_token: SecretStr
    hq_bot_username: str = "IDOLHQBot"

    # ── Founder ──────────────────────────────────────────
    # The ONLY way to define the Founder identity.
    # Cannot be changed via bot operations.
    founder_telegram_id: int

    # ── Staff ────────────────────────────────────────────
    # Optional pre-configured Owner Telegram IDs.
    # Can also be assigned at runtime by Founder.
    owner_telegram_ids: list[int] = []

    # ── IDOL Team Group ──────────────────────────────────
    idol_team_group_id: int | None = None
    topic_system_id: int | None = None
    topic_orders_id: int | None = None
    topic_customers_id: int | None = None
    topic_staff_id: int | None = None

    # ── Database ─────────────────────────────────────────
    database_url: SecretStr

    # ── AI (disabled for V1) ─────────────────────────────
    enable_ai: bool = False
    groq_api_key: SecretStr | None = None
    ai_model: str = "openai/gpt-oss-120b"

    # ── Validators ───────────────────────────────────────

    @field_validator("owner_telegram_ids", mode="before")
    @classmethod
    def parse_owner_ids(cls, v: str | list[int]) -> list[int]:
        if isinstance(v, str):
            if not v.strip():
                return []
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        return v

    @field_validator("founder_telegram_id", mode="before")
    @classmethod
    def validate_founder_id(cls, v: int | str) -> int:
        val = int(v)
        if val <= 0:
            raise ValueError("FOUNDER_TELEGRAM_ID must be a positive integer")
        return val

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


# Singleton — import this everywhere
settings = Settings()  # type: ignore[call-arg]
