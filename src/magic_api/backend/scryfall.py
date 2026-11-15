"""Async Scryfall API client (paced, identifying User-Agent)."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import httpx

from magic_api.utils.config import get_config
from magic_api.utils.models import Card, CardSearchResponse

logger = logging.getLogger(__name__)


class ScryfallError(Exception):
    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.status_code = status_code


_client: httpx.AsyncClient | None = None
_rate_lock = asyncio.Lock()
_last_call_ts: float = 0.0


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        cfg = get_config().backend
        _client = httpx.AsyncClient(
            base_url=cfg.scryfall_api_base,
            headers={"User-Agent": cfg.scryfall_user_agent, "Accept": "application/json"},
            timeout=httpx.Timeout(15.0),
        )
    return _client


async def _paced_get(path: str, params: dict[str, Any] | None = None) -> httpx.Response:
    global _last_call_ts
    min_delay = get_config().backend.scryfall_min_delay_ms / 1000.0
    async with _rate_lock:
        elapsed = time.monotonic() - _last_call_ts
        if elapsed < min_delay:
            await asyncio.sleep(min_delay - elapsed)
        resp = await _get_client().get(path, params=params)
        _last_call_ts = time.monotonic()
    return resp


async def search(query: str, page: int = 1, unique: str = "cards") -> CardSearchResponse:
    """Hit /cards/search. A 404 (no matches) becomes an empty result."""
    resp = await _paced_get(
        "/cards/search", params={"q": query, "page": page, "unique": unique}
    )
    if resp.status_code == 404:
        return CardSearchResponse()
    if resp.status_code >= 400:
        raise ScryfallError(
            f"Scryfall error {resp.status_code}: {resp.text[:200]}",
            status_code=resp.status_code,
        )
    payload = resp.json()
    return CardSearchResponse(
        total_cards=payload.get("total_cards", 0),
        has_more=payload.get("has_more", False),
        next_page=payload.get("next_page"),
        data=[Card.model_validate(c) for c in payload.get("data", [])],
    )


async def close() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
