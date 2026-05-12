"""Request/response models for the /chat endpoint."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.models.card import Card

Role = Literal["user", "assistant"]
Mode = Literal["cards", "rules"]


class ChatMessage(BaseModel):
    role: Role
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(
        ...,
        description="Full conversation so far, oldest first.",
        min_length=1,
    )
    # Phase 1 only implements "cards". "rules" is reserved for Phase 2.
    mode: Mode = Field(default="cards", description="Conversational context.")
    # Optional caller-supplied preferences (favorite colors, archetype, etc.)
    # We surface these into the system prompt — they should never override
    # the topic guardrails.
    preferences: dict[str, str] | None = None


class ChatResponse(BaseModel):
    reply: str = Field(..., description="Final assistant message text.")
    cards: list[Card] = Field(
        default_factory=list,
        description="Cards that were surfaced during the turn, in display order.",
    )
    stop_reason: str | None = None
