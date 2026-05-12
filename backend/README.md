# MagicGPT Backend (FastAPI)

The API layer for MagicGPT. Wraps the [Scryfall](https://scryfall.com/docs/api)
card data API and brokers conversations with Anthropic Claude using
[tool use](https://docs.claude.com/en/docs/build-with-claude/tool-use) so the
model can ask Scryfall for cards on demand.

## Quick start

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env — set ANTHROPIC_API_KEY

uvicorn app.main:app --reload
```

Then visit:

- `http://localhost:8000/docs` — interactive Swagger UI
- `http://localhost:8000/health` — liveness check

## Project layout

```
app/
  main.py              FastAPI factory, CORS, route mounting
  config.py            pydantic-settings Settings loaded from env
  api/
    routes/
      chat.py          POST /chat — main conversational endpoint
      cards.py         GET  /cards/search — thin Scryfall passthrough
      health.py        GET  /health
  services/
    claude.py          Anthropic client + tool-use loop
    scryfall.py        Async Scryfall client (httpx) with rate-limit pacing
    guardrails.py      Topic-policy checks (off-topic / harm refusal)
  models/
    card.py            Pydantic models for Scryfall card payloads
    chat.py            Request/response models for /chat
  prompts/
    system.py          System prompt assembling MTG focus + guardrails
  etl/
    scryfall_bulk.py   Skeleton for ingesting Scryfall bulk data (Phase 1 ETL)
tests/                 pytest suite (uses respx to mock Scryfall)
```

## How the chat flow works

1. Client `POST /chat` with `messages: [...]` and optional `mode`
   (`"cards"` for now; `"rules"` later).
2. `guardrails.check_inbound` filters off-topic prompts.
3. `claude.run_conversation` runs Claude with the `scryfall_search` tool
   exposed. If Claude wants cards, it emits a tool_use; the backend calls
   `scryfall.search`, returns the result, and Claude continues.
4. The final assistant message plus any cards Claude referenced are returned
   so the UI can render a card grid alongside the text.

## Testing

```bash
pytest
```

Scryfall calls are mocked with `respx`, so tests do not hit the live API.
