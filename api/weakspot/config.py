"""Runtime configuration.

Every knob the spec calls out (rate limits, code size caps, model tiers, latency
targets) lives here so the numbers in the README have exactly one source.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "development"

    database_url: str = "postgresql+psycopg://weakspot:weakspot@localhost:5432/weakspot"
    redis_url: str = "redis://localhost:6379/0"

    taxonomy_path: Path = Path(__file__).resolve().parents[2] / "taxonomy" / "patterns.yaml"

    # --- auth ---
    session_secret: str = "dev-only-not-a-real-secret"
    session_cookie: str = "weakspot_session"
    session_max_age: int = 60 * 60 * 24 * 14
    github_client_id: str = ""
    github_client_secret: str = ""
    github_callback_url: str = "http://localhost:8000/api/v1/auth/github/callback"
    web_origin: str = "http://localhost:5173"
    # Mints a local session without GitHub. Refused outright when env == production.
    dev_auth_bypass: bool = False

    # --- models ---
    anthropic_api_key: str = ""
    voyage_api_key: str = ""
    # Cheapest capable tier by default; escalate to the strong tier once, on verifier
    # rejection only. Haiku 4.5 rejects `effort`; Opus 5 runs adaptive thinking by default.
    model_tier_cheap: str = "claude-haiku-4-5"
    model_tier_strong: str = "claude-opus-5"
    model_tier_verifier: str = "claude-haiku-4-5"
    model_tier_judge: str = "claude-haiku-4-5"
    embedding_model: str = "voyage-3"
    embedding_dim: int = 1024

    # --- limits (spec section 7) ---
    free_diagnoses_per_day: int = 10
    max_code_bytes: int = 32 * 1024
    max_code_lines: int = 800
    max_retries: int = 1  # escalate once, per spec
    mcp_list_cap: int = 20

    # --- observability ---
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    @property
    def is_production(self) -> bool:
        return self.env.lower() in {"production", "prod"}

    @property
    def llm_enabled(self) -> bool:
        return bool(self.anthropic_api_key)

    @property
    def embeddings_enabled(self) -> bool:
        return bool(self.voyage_api_key)


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    if s.is_production and s.dev_auth_bypass:
        raise RuntimeError("DEV_AUTH_BYPASS must never be enabled in production")
    return s
