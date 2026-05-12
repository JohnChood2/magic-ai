"""Application settings loaded from environment / .env.

We use pydantic-settings so config is typed and validated at startup
rather than blowing up at request time when a missing key is hit.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Anthropic ---
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-sonnet-4-6", alias="ANTHROPIC_MODEL")

    # --- Scryfall ---
    scryfall_api_base: str = Field(
        default="https://api.scryfall.com", alias="SCRYFALL_API_BASE"
    )
    scryfall_user_agent: str = Field(
        default="MagicGPT/0.1 (+https://github.com/your-org/magic-ai)",
        alias="SCRYFALL_USER_AGENT",
    )
    # Scryfall asks fan projects to pace requests; 150ms between calls is
    # their recommended floor. We'll enforce this in the client.
    scryfall_min_delay_ms: int = Field(default=150, alias="SCRYFALL_MIN_DELAY_MS")

    # --- Server ---
    cors_allowed_origins: str = Field(
        default="http://localhost:3000", alias="CORS_ALLOWED_ORIGINS"
    )
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    env: str = Field(default="development", alias="ENV")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached so we read the env once per process."""
    return Settings()
