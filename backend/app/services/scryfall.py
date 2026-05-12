"""Async Scryfall API client.

Scryfall's API is free and public, but they ask fan projects to:
  * Send an identifying User-Agent
  * Pace requests (at least 50–100ms between calls, 10/sec hard ceiling)

See: https://scryfall.com/docs/api

This module is intentionally thin — we keep one global httpx.AsyncClient and
serialize requests through an asyncio.Lock + small delay so we play nice
under load.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import httpx

from app.config import get_settings
from app.models.card import Card, CardSearchResponse

logger = logging.getLogger(__name__)


class ScryfallError(Exception):
    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.status_code = status_code


# Module-level singletons. Reusing the client gives us connection pooling.
_client: httpx.AsyncClient | None = None
_rate_lock = asyncio.Lock()
_last_call_ts: float = 0.0


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        settings = get_settings()
        _client = httpx.AsyncClient(
            base_url=settings.scryfall_api_base,
            headers={
                "User-Agent": settings.scryfall_user_agent,
                "Accept": "application/json",
            },
            timeout=httpx.Timeout(15.0),
        )
    return _client


async def _paced_get(path: str, params: dict[str, Any] | None = None) -> httpx.Response:
    """GET with the rate-limit pacing Scryfall asks fan projects to honor."""
    global _last_call_ts
    settings = get_settings()
    min_delay = settings.scryfall_min_delay_ms / 1000.0

    async with _rate_lock:
        elapsed = time.monotonic() - _last_call_ts
        if elapsed < min_delay:
            await asyncio.sleep(min_delay - elapsed)
        resp = await _get_client().get(path, params=params)
        _last_call_ts = time.monotonic()
    return resp


async def search(
    query: str,
    page: int = 1,
    unique: str = "cards",
) -> CardSearchResponse:
    """Hit /cards/search and normalize the envelope.

    Scryfall returns 404 with `object: "error"` for no-match queries — we
    treat that as an empty result set rather than an error, so the chat
    layer can render 'no cards found' cleanly.
    """
    params = {"q": query, "page": page, "unique": unique}
    resp = await _paced_get("/cards/search", params=params)

    if resp.status_code == 404:
        logger.info("Scryfall search returned no results for query=%r", query)
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
        raw=payload,
    )


async def named(name: str, fuzzy: bool = True) -> Card | None:
    """Look up a single card by exact or fuzzy name. None if not found."""
    params = {"fuzzy": name} if fuzzy else {"exact": name}
    resp = await _paced_get("/cards/named", params=params)
    if resp.status_code == 404:
        return None
    if resp.status_code >= 400:
        raise ScryfallError(
            f"Scryfall error {resp.status_code}: {resp.text[:200]}",
            status_code=resp.status_code,
        )
    return Card.model_validate(resp.json())


async def close() -> None:
    """Shut the httpx client down — called from app shutdown hooks/tests."""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
