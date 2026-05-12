"""Anthropic Claude client + tool-use loop.

We expose a single tool, `scryfall_search`, that lets Claude ask Scryfall
for cards on demand. The loop is bounded by `MAX_TURNS` to prevent runaway
tool-call cycles.

References:
  https://docs.claude.com/en/docs/build-with-claude/tool-use
"""

from __future__ import annotations

import logging
from typing import Any

from anthropic import APIError, AsyncAnthropic

from app.config import get_settings
from app.models.card import Card
from app.models.chat import ChatRequest, ChatResponse
from app.prompts.system import build_system_prompt
from app.services import scryfall

logger = logging.getLogger(__name__)

MAX_TURNS = 5  # safety ceiling on tool_use roundtrips per request
MAX_CARDS_RETURNED_TO_MODEL = 12  # don't blow the context window on huge result sets


class ClaudeError(Exception):
    """Raised when the upstream Anthropic call fails."""


SCRYFALL_TOOL: dict[str, Any] = {
    "name": "scryfall_search",
    "description": (
        "Search the Scryfall card database using Scryfall search syntax "
        "(see https://scryfall.com/docs/syntax). Returns up to "
        f"{MAX_CARDS_RETURNED_TO_MODEL} matching cards with name, mana cost, "
        "type line, oracle text, and color identity. Use this any time the "
        "user asks about specific cards, card types, abilities, or for "
        "deck-building suggestions."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "Scryfall search query, e.g. 'c:u t:creature o:flying "
                    "cmc<=3 f:commander'."
                ),
            },
            "page": {
                "type": "integer",
                "description": "Page number (default 1).",
                "minimum": 1,
            },
        },
        "required": ["query"],
    },
}


_client: AsyncAnthropic | None = None


def _get_client() -> AsyncAnthropic:
    global _client
    if _client is None:
        settings = get_settings()
        if not settings.anthropic_api_key:
            raise ClaudeError("ANTHROPIC_API_KEY is not set.")
        _client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _client


def _card_for_model(card: Card) -> dict[str, Any]:
    """Compact card dict for the LLM — strips image URLs etc. to save tokens."""
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
    """Execute scryfall_search and return (tool_result_text, cards_for_ui)."""
    query = tool_input.get("query", "")
    page = int(tool_input.get("page", 1))
    try:
        result = await scryfall.search(query=query, page=page)
    except scryfall.ScryfallError as exc:
        return (f"Scryfall error: {exc}", [])

    cards = result.data[:MAX_CARDS_RETURNED_TO_MODEL]
    summary = {
        "total_cards": result.total_cards,
        "returned": len(cards),
        "has_more": result.has_more,
        "cards": [_card_for_model(c) for c in cards],
    }
    # Tool results are returned as strings to Claude. JSON works fine.
    import json

    return json.dumps(summary), cards


async def run_conversation(request: ChatRequest) -> ChatResponse:
    """Run a bounded tool-use loop and return the final assistant message."""
    settings = get_settings()
    client = _get_client()

    system_prompt = build_system_prompt(
        mode=request.mode, preferences=request.preferences
    )
    # Build Anthropic-shaped message history.
    messages: list[dict[str, Any]] = [
        {"role": m.role, "content": m.content} for m in request.messages
    ]

    # Cards Claude surfaced this turn, dedup'd by id, preserving first-seen order.
    surfaced: dict[str, Card] = {}

    for _turn in range(MAX_TURNS):
        try:
            response = await client.messages.create(
                model=settings.anthropic_model,
                system=system_prompt,
                tools=[SCRYFALL_TOOL],
                messages=messages,
                max_tokens=1024,
            )
        except APIError as exc:  # network / 5xx / auth
            logger.exception("Anthropic API error")
            raise ClaudeError(str(exc)) from exc

        # No tool calls → we have the final answer.
        if response.stop_reason != "tool_use":
            text = _extract_text(response.content)
            return ChatResponse(
                reply=text,
                cards=list(surfaced.values()),
                stop_reason=response.stop_reason,
            )

        # Echo the assistant turn (incl. tool_use blocks) into history.
        messages.append({"role": "assistant", "content": response.content})

        # Run every tool_use block in this turn.
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
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": text,
                }
            )

        messages.append({"role": "user", "content": tool_results})

    # Tool-use loop didn't converge in time. Return what we have.
    logger.warning("Hit MAX_TURNS=%d in tool-use loop", MAX_TURNS)
    return ChatResponse(
        reply=(
            "I had to stop early — I made too many lookups in a row without "
            "settling on an answer. Could you rephrase or narrow the question?"
        ),
        cards=list(surfaced.values()),
        stop_reason="max_turns",
    )


def _extract_text(content: list[Any]) -> str:
    """Pull text blocks out of an Anthropic message; ignore others."""
    parts: list[str] = []
    for block in content:
        if getattr(block, "type", None) == "text":
            parts.append(block.text)
    return "\n\n".join(parts).strip()
