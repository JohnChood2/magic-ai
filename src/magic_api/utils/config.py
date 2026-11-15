"""Loads ``config.yaml`` and exposes typed settings for every service.

Callers should import from here instead of reading the YAML themselves::

    from magic_api.utils.config import get_config, service_url

    cfg = get_config()
    cfg.backend.port
    service_url("ai")          # -> "http://127.0.0.1:8001"
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel

PACKAGE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PACKAGE_DIR / "config.yaml"
PROJECT_ROOT = PACKAGE_DIR.parents[1]  # <repo>/src/magic_api -> <repo>

ServiceName = Literal["ui", "backend", "ai", "database"]


class ServiceConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int
    database_url: str


class UIConfig(ServiceConfig):
    pass


class BackendConfig(ServiceConfig):
    scryfall_api_base: str = "https://api.scryfall.com"
    scryfall_user_agent: str = "MagicGPT/0.1 (+https://github.com/your-org/magic-ai)"
    scryfall_min_delay_ms: int = 150
    log_level: str = "INFO"


class AIConfig(ServiceConfig):
    model: str = "claude-sonnet-5-5"
    max_tokens: int = 1024
    max_turns: int = 5
    max_cards_returned_to_model: int = 12


class DatabaseConfig(ServiceConfig):
    pass


class AppConfig(BaseModel):
    ui: UIConfig
    backend: BackendConfig
    ai: AIConfig
    database: DatabaseConfig


def config_path() -> Path:
    return Path(os.environ.get("MAGIC_API_CONFIG", DEFAULT_CONFIG_PATH))


@lru_cache
def get_config() -> AppConfig:
    """Parse the YAML once per process."""
    with config_path().open() as fp:
        return AppConfig.model_validate(yaml.safe_load(fp))


def service_url(name: ServiceName) -> str:
    """Base URL other services/browsers use to reach ``name``."""
    svc: ServiceConfig = getattr(get_config(), name)
    host = "127.0.0.1" if svc.host in ("0.0.0.0", "::") else svc.host  # noqa: S104
    return f"http://{host}:{svc.port}"


def sqlite_path(database_url: str) -> Path:
    """Turn ``sqlite:///rel/or/abs.db`` into a filesystem path."""
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        raise ValueError(f"Only sqlite:/// URLs are supported, got {database_url!r}")
    path = Path(database_url[len(prefix):])
    return path if path.is_absolute() else PROJECT_ROOT / path
