"""Inbound topic/safety guardrails (cheap deterministic first layer).

The AI service's system prompt is the second layer. Keeps the bot on Magic:
no medical/legal/financial advice and no relationship-style bonding.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from magic_api.utils.models import ChatMessage

_OFF_TOPIC_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("medical topics", re.compile(r"\b(medical|diagnos\w*|prescription|dosage|symptoms?)\b", re.I)),
    ("legal topics", re.compile(r"\b(legal advice|sue|lawsuit|attorney|lawyer)\b", re.I)),
    ("financial topics", re.compile(r"\b(invest|stocks?|crypto|portfolio|tax advice)\b", re.I)),
    (
        "personal relationships",
        re.compile(
            r"\b(i love you|are you (my )?(girlfriend|boyfriend|partner)|"
            r"be my (girlfriend|boyfriend|friend|therapist))\b",
            re.I,
        ),
    ),
)

# MTG vocabulary biases toward allowing a message that brushes a pattern.
_MTG_TERMS: tuple[str, ...] = (
    "magic", "mtg", "commander", "edh", "scryfall", "card", "deck",
    "mana", "creature", "planeswalker", "instant", "sorcery", "enchantment",
    "artifact", "land", "tapped", "untap", "graveyard", "library",
    "battlefield", "exile", "lifelink", "deathtouch", "trample", "vigilance",
    "flying", "menace", "edhrec", "moxfield", "archidekt", "gatherer",
)

REFUSAL_TEMPLATE = (
    "I'm MagicGPT. I can only help with Magic: The Gathering questions "
    "(cards, Commander deck building, the rules, etc.). I can't help with "
    "{topic}. Want to ask about a card or deck instead?"
)


def check_inbound(messages: Iterable[ChatMessage]) -> str | None:
    """Return a refusal string if the latest user turn is off-topic, else None."""
    last_user = next((m for m in reversed(list(messages)) if m.role == "user"), None)
    if last_user is None:
        return None
    text = last_user.content
    lower = text.lower()
    if any(term in lower for term in _MTG_TERMS):
        return None
    for topic, pattern in _OFF_TOPIC_PATTERNS:
        if pattern.search(text):
            return REFUSAL_TEMPLATE.format(topic=topic)
    return None
