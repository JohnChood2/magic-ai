# MagicGPT — Architecture

> "Hello, world" scaffolding for the Phase 1 goals in the project
> [`README.md`](../README.md): card-search and Commander deck-building
> chatbot, with room to add a rules-Q&A mode in Phase 2.

## High-level diagram

```
                              ┌──────────────────────────┐
   Browser  ──HTTPS──▶  Next.js (frontend, :3000)
   (Chat UI)            │  app/page.tsx → Chat.tsx
                        │  app/api/chat/route.ts (proxy)
                        └──────────────┬───────────────┘
                                       │ POST /chat
                                       ▼
                              ┌──────────────────────────┐
                              │   FastAPI (backend, :8000)
                              │   ├─ api/routes/chat.py
                              │   ├─ services/guardrails.py
                              │   ├─ services/claude.py  ──▶ Anthropic API
                              │   └─ services/scryfall.py ─▶ Scryfall API
                              └──────────────────────────┘
```

## Request lifecycle (chat)

1. **User types a message** in `Chat.tsx`. The component appends to local
   state and POSTs the full conversation to `/api/chat`.
2. **Next.js proxy** (`app/api/chat/route.ts`) forwards the JSON body to
   `${BACKEND_URL}/chat` server-side. The browser never learns the
   backend URL.
3. **FastAPI `/chat`** runs `guardrails.check_inbound`. Pattern-matched
   off-topic prompts (medical/legal/financial/relationship) get an instant
   refusal — no LLM call.
4. **Claude tool-use loop** (`services/claude.py`):
   - Calls `client.messages.create` with the `scryfall_search` tool exposed.
   - If Claude emits a `tool_use` block, we execute `scryfall.search`,
     hand the JSON back as a `tool_result`, and loop. Bounded by
     `MAX_TURNS = 5`.
   - Once Claude stops with anything other than `tool_use`, we return.
5. **Response**: `{ reply, cards, stop_reason }`. The frontend renders
   `reply` as a chat bubble and chooses a card layout based on count.

## Card display rules (from the README)

| Result size | Component         |
| ----------- | ----------------- |
| 0           | (just text)       |
| 1 – 4       | `CardGrid`        |
| 5 – 20      | `CardList` (hover image) |
| 21+         | `CardList` truncated to 20 + "narrow your query / open Scryfall" hint |

These are also enforced server-side: the Claude service caps the number of
cards passed back to the model at `MAX_CARDS_RETURNED_TO_MODEL = 12` to
protect the context window.

## Scryfall integration

- We use the **live `/cards/search` API** for Phase 1. It's free, fast, and
  handles paginated queries — no local index needed yet.
- We send an identifying `User-Agent` (configurable) and pace requests to
  ≥ 150 ms between calls, per Scryfall's published guidance.
- **Bulk-data ETL** (`app/etl/scryfall_bulk.py`) is a skeleton, intended
  to be wired into a real datastore when we move past pure pass-through
  (vector search over Oracle text, custom tagging, EDHREC-style stats).

## Guardrails

Two layers:

1. **Inbound regex** (`services/guardrails.py`) — kills the obvious cases
   before they cost us an LLM call. Tuned conservatively so MTG terms
   override false positives.
2. **System prompt** (`prompts/system.py`) — instructs Claude to refuse
   off-topic asks and never claim to be human / form a relationship.

When in doubt, add to the system prompt rather than the regex. Regex
catches the cheap cases; the model catches the rest.

## Configuration

All settings live in `backend/app/config.py` (pydantic-settings).
`.env` overrides; `.env.example` documents every key.

| Key | Default | Notes |
| --- | ------- | ----- |
| `ANTHROPIC_API_KEY` | — | required |
| `ANTHROPIC_MODEL`   | `claude-sonnet-4-6` | swap to `claude-opus-4-6` for higher quality, `claude-haiku-4-5-20251001` for speed |
| `SCRYFALL_USER_AGENT` | `MagicGPT/0.1 (…)` | identifies us to Scryfall |
| `SCRYFALL_MIN_DELAY_MS` | `150` | pacing between calls |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:3000` | comma-separated |

## Deployment notes (future)

- **Backend**: containerized via `backend/Dockerfile`. Render, Fly.io, or
  Cloud Run all work for a low-traffic prototype. Scryfall rate-limits are
  per-IP, so a single instance is fine to start.
- **Frontend**: Vercel deploys Next.js out of the box. Set `BACKEND_URL`
  in Vercel project env vars.
- **Costs**: Anthropic per-token cost is the dominant variable. The tool-use
  loop is bounded (`MAX_TURNS`) to keep the worst case predictable.

## Things we explicitly haven't built yet (and where they go)

| Feature | Where it slots in |
| ------- | ----------------- |
| Streaming chat responses | switch `claude.run_conversation` to `client.messages.stream` and adopt SSE in the Next.js route. |
| Local card index / vector search | flesh out `app/etl/scryfall_bulk.py` and add a `services/index.py`. |
| Rules-Q&A mode (Phase 2) | new tool (`rules_lookup`) in `claude.py` + `_RULES_ADDENDUM` already in `prompts/system.py`. |
| User accounts / saved chats | add `app/api/routes/auth.py` and a real DB. |
| Deck import (Moxfield/Archidekt) | new endpoint that fetches and parses their public list APIs, then feeds into the system prompt as deck context. |
| TS types generated from Pydantic | hook up `datamodel-code-generator --output-model-type typescript`. |
