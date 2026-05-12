"""Shared pytest fixtures.

We:
  * Force a deterministic Settings (no .env required) so tests run in CI.
  * Provide a FastAPI TestClient.
  * Auto-reset the scryfall module's global client between tests.
"""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session", autouse=True)
def _set_env() -> None:
    os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
    os.environ.setdefault("ANTHROPIC_MODEL", "claude-sonnet-4-6")
    os.environ.setdefault("SCRYFALL_API_BASE", "https://api.scryfall.test")
    os.environ.setdefault("SCRYFALL_MIN_DELAY_MS", "0")
    os.environ.setdefault("ENV", "test")
    # Strip any proxy env vars so httpx doesn't try to route mocked requests
    # through a real proxy in CI/dev sandboxes.
    for var in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
                "http_proxy", "https_proxy", "all_proxy"):
        os.environ.pop(var, None)


@pytest.fixture
def client() -> TestClient:
    # Imported lazily so env vars above are in place when Settings is built.
    from app.main import create_app

    return TestClient(create_app())


@pytest.fixture(autouse=True)
async def _reset_scryfall_client():
    from app.services import scryfall

    yield
    await scryfall.close()
