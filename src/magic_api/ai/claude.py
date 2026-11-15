"""Anthropic Claude client and bounded tool-use loop.

Claude gets one tool, `scryfall_search`, which this service executes by
calling the backend's `/cards/search` endpoint.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

import httpx
from anthropic import APIError, AsyncAnthropic

from magic_api.ai.prompts import build_system_prompt
from magic_api.utils.config import get_config, service_url
from magic_api.utils.models import Card, CardSearchResponse, ChatRequest, ChatResponse

logger = logging.getLogger(__name__)


class ClaudeError(Exception):
    """Raised when the upstream Anthropic call fails."""


def _scryfall_tool() -> dict[str, Any]:
    limit = get_config().ai.max_cards_returned_to_model
    return {
        "name": "scryfall_search",
        "description": (
            "Search the Scryfall card database using Scryfall search syntax "
            f"(https://scryfall.com/docs/syntax). Returns up to {limit} matching "
            "cards with name, mana cost, type line, oracle text and color identity."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Scryfall query, e.g. 'c:u t:creature o:flying cmc<=3 f:commander'.",
                },
                "page": {"type": "integer", "description": "Page number (default 1).", "minimum": 1},
            },
            "required": ["query"],
        },
    }


_client: AsyncAnthropic | None = None


def _get_client() -> AsyncAnthropic:
    global _client
    if _client is None:
        key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not key:
            raise ClaudeError("ANTHROPIC_API_KEY is not set.")
        _client = AsyncAnthropic(api_key=key)
    return _client


def _card_for_model(card: Card) -> dict[str, Any]:
    """Compact card dict for the LLM; strips image URLs to save tokens."""
    return {
        "name": card.name,
        "mana_cost": card.mana_cost,
        "type_line": card.type_line,
        "oracle_text": card.oracle_text,
        "color_identity": card.color_identity,
        "power": card.power,
        "toughness": card.toughness,
        "rarity": card.rarity,
        "set": card.set,
    }


async def _run_tool(tool_input: dict[str, Any]) -> tuple[str, list[Card]]:
    """Run scryfall_search via the backend; returns (tool_result_text, cards_for_ui)."""
    limit = get_config().ai.max_cards_returned_to_model
    params = {"q": tool_input.get("query", ""), "page": int(tool_input.get("page", 1))}
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(f"{service_url('backend')}/cards/search", params=params)
        if resp.status_code >= 400:
            return f"Card search error {resp.status_code}: {resp.text[:200]}", []
        result = CardSearchResponse.model_validate(resp.json())
    except httpx.HTTPError as exc:
        return f"Card search unavailable: {exc}", []

    cards = result.data[:limit]
    summary = {
        "total_cards": result.total_cards,
        "returned": len(cards),
        "has_more": result.has_more,
        "cards": [_card_for_model(c) for c in cards],
    }
    return json.dumps(summary), cards


def _extract_text(content: list[Any]) -> str:
    return "\n\n".join(b.text for b in content if getattr(b, "type", None) == "text").strip()


async def run_conversation(request: ChatRequest) -> ChatResponse:
    cfg = get_config().ai
    client = _get_client()
    system_prompt = build_system_prompt(mode=request.mode, preferences=request.preferences)
    messages: list[dict[str, Any]] = [
        {"role": m.role, "content": m.content} for m in request.messages
    ]
    surfaced: dict[str, Card] = {}  # dedup by id, first-seen order

    for _ in range(cfg.max_turns):
        try:
            response = await client.messages.create(
                model=cfg.model,
                system=system_prompt,
                tools=[_scryfall_tool()],
                messages=messages,
                max_tokens=cfg.max_tokens,
            )
        except APIError as exc:
            logger.exception("Anthropic API error")
            raise ClaudeError(str(exc)) from exc

        if response.stop_reason != "tool_use":
            return ChatResponse(
                reply=_extract_text(response.content),
                cards=list(surfaced.values()),
                stop_reason=response.stop_reason,
            )

        messages.append({"role": "assistant", "content": response.content})
        tool_results: list[dict[str, Any]] = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            if block.name != "scryfall_search":
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": f"Unknown tool: {block.name}",
                        "is_error": True,
                    }
                )
                continue
            text, cards = await _run_tool(block.input)
            for c in cards:
                surfaced.setdefault(c.id, c)
            tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": text})
        messages.append({"role": "user", "content": tool_results})

    logger.warning("Hit max_turns=%d in tool-use loop", cfg.max_turns)
    return ChatResponse(
        reply=(
            "I had to stop early: I made too many lookups in a row without "
            "settling on an answer. Could you rephrase or narrow the question?"
        ),
        cards=list(surfaced.values()),
        stop_reason="max_turns",
    )
