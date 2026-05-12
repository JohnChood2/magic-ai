"""Topic and safety guardrails.

The product brief says:
  * Keep the agent focused on Magic: The Gathering.
  * Don't dispense medical/legal/financial advice.
  * Don't let users form a parasocial / relationship-style bond with the bot.

We do two layers of defense:
  1. **Inbound checks** here — pattern matches that catch the obvious cases
     before we even call the LLM. Cheap and deterministic.
  2. **System prompt** in `app.prompts.system` — instructs Claude to refuse
     off-topic asks. This catches everything pattern-matching misses.

This module is intentionally simple. The list is meant to be tuned over time
based on real abuse logs, not exhaustive on day one.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from app.models.chat import ChatMessage

# Phrases that almost always mean the user is asking for something we should
# decline. Case-insensitive substring/regex match against the latest user turn.
_OFF_TOPIC_PATTERNS: tuple[re.Pattern[str], ...] = (
    # Health / medical
    re.compile(r"\b(medical|diagnos\w*|prescription|dosage|symptoms?)\b", re.I),
    # Legal
    re.compile(r"\b(legal advice|sue|lawsuit|attorney|lawyer)\b", re.I),
    # Financial
    re.compile(r"\b(invest|stocks?|crypto|portfolio|tax advice)\b", re.I),
    # Relationship / parasocial
    re.compile(
        r"\b(i love you|are you (my )?(girlfriend|boyfriend|partner)|"
        r"be my (girlfriend|boyfriend|friend|therapist))\b",
        re.I,
    ),
)

# If any of these MTG-specific terms show up, we bias toward allowing the
# message even if it brushes one of the patterns above (e.g. "Lifelink keyword"
# might look like a health term).
_MTG_TERMS: tuple[str, ...] = (
    "magic", "mtg", "commander", "edh", "scryfall", "card", "deck",
    "mana", "creature", "planeswalker", "instant", "sorcery", "enchantment",
    "artifact", "land", "tapped", "untap", "graveyard", "library",
    "battlefield", "exile", "lifelink", "deathtouch", "trample", "vigilance",
    "flying", "menace", "edhrec", "moxfield", "archidekt", "gatherer",
)


REFUSAL_TEMPLATE = (
    "I'm MagicGPT — I can only help with Magic: The Gathering questions "
    "(cards, Commander deck building, the rules, etc.). I can't help with "
    "{topic}. Want to ask about a card or deck instead?"
)


def _looks_mtg(text: str) -> bool:
    lower = text.lower()
    return any(term in lower for term in _MTG_TERMS)


def _topic_label(text: str) -> str:
    for pat in _OFF_TOPIC_PATTERNS:
        if pat.search(text):
            return pat.pattern.split("|")[0].strip("\\b()")
    return "that"


def check_inbound(messages: Iterable[ChatMessage]) -> str | None:
    """Return a refusal string if the latest user turn is off-topic, else None.

    We only look at the last user message — earlier turns may legitimately
    contain context that pattern-matches but is fine in context.
    """
    last_user = next(
        (m for m in reversed(list(messages)) if m.role == "user"), None
    )
    if last_user is None:
        return None

    text = last_user.content
    if _looks_mtg(text):
        return None

    for pat in _OFF_TOPIC_PATTERNS:
        if pat.search(text):
            return REFUSAL_TEMPLATE.format(topic=_topic_label(text))

    return None
