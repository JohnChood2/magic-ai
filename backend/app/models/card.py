"""Pydantic models for Scryfall card data.

We only model the fields we actually use in the UI. The full Scryfall card
object has ~80 fields (see https://scryfall.com/docs/api/cards). The raw
payload is also passed through in `Card.extra` for forward compatibility.
"""

from __future__ import annotations

from typing import Any

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
    # Commander-relevant legality
    legalities: dict[str, str] = Field(default_factory=dict)


class CardSearchResponse(BaseModel):
    """Normalized envelope around Scryfall's /cards/search response."""

    total_cards: int = 0
    has_more: bool = False
    next_page: str | None = None
    data: list[Card] = Field(default_factory=list)
    # Pass through anything we did not model so the frontend can degrade
    # gracefully if Scryfall adds new fields.
    raw: dict[str, Any] | None = None
