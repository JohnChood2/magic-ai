"""Pydantic models shared by all services (cards and chat payloads)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class CardImageUris(BaseModel):
    small: str | None = None
    normal: str | None = None
    large: str | None = None
    png: str | None = None
    art_crop: str | None = None
    border_crop: str | None = None


class CardFace(BaseModel):
    """One face of a double-faced/transform card."""

    name: str
    mana_cost: str | None = None
    type_line: str | None = None
    oracle_text: str | None = None
    power: str | None = None
    toughness: str | None = None
    image_uris: CardImageUris | None = None


class Card(BaseModel):
    """A single Scryfall card, normalized for our UI."""

    id: str
    oracle_id: str | None = None
    name: str
    mana_cost: str | None = None
    cmc: float | None = None
    type_line: str | None = None
    oracle_text: str | None = None
    colors: list[str] | None = None
    color_identity: list[str] | None = None
    power: str | None = None
    toughness: str | None = None
    loyalty: str | None = None
    rarity: str | None = None
    set: str | None = None
    set_name: str | None = None
    collector_number: str | None = None
    image_uris: CardImageUris | None = None
    card_faces: list[CardFace] | None = None
    scryfall_uri: str | None = None
    legalities: dict[str, str] = Field(default_factory=dict)


class CardSearchResponse(BaseModel):
    """Normalized envelope around a card search result."""

    total_cards: int = 0
    has_more: bool = False
    next_page: str | None = None
    data: list[Card] = Field(default_factory=list)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(
        ..., min_length=1, description="Full conversation so far, oldest first."
    )
    mode: Literal["cards", "rules"] = Field(
        default="cards",
        description="Conversational context. Only 'cards' is implemented in Phase 1.",
    )
    preferences: dict[str, str] | None = Field(
        default=None,
        description="Optional user preferences surfaced into the system prompt.",
    )


class ChatResponse(BaseModel):
    reply: str = Field(..., description="Final assistant message text.")
    cards: list[Card] = Field(
        default_factory=list,
        description="Cards surfaced during the turn, in display order.",
    )
    stop_reason: str | None = None


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str
    version: str
    details: dict[str, Any] = Field(default_factory=dict)
