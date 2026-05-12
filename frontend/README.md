# MagicGPT Frontend (Next.js)

Chat UI for MagicGPT. Talks to the FastAPI backend via a server-side
`/api/chat` route so the Anthropic key (or any future auth) never touches
the browser.

## Quick start

```bash
cd frontend
npm install
cp .env.example .env.local
# edit BACKEND_URL if your API isn't on localhost:8000

npm run dev
```

Open http://localhost:3000.

## Layout

```
app/
  layout.tsx        root layout, fonts, global CSS
  page.tsx          main chat page
  globals.css       Tailwind base + a few utilities
  api/chat/route.ts proxy to FastAPI /chat
components/
  Chat.tsx          state machine for the conversation
  Message.tsx       single message bubble (renders markdown-ish text)
  CardGrid.tsx      4-up grid for small result sets
  CardList.tsx      bulleted list w/ hover-image for big result sets
  CardThumb.tsx     reusable card thumbnail
  Header.tsx        app chrome + mode toggle (cards | rules later)
lib/
  api.ts            typed fetch wrapper for /api/chat
  types.ts          shared TS types matching backend Pydantic models
```

## Display rules (from the README)

- **≤ 4 cards** → render as `<CardGrid>`.
- **5–20 cards** → render as `<CardList>` (bulleted, hover shows image).
- **More than that** → list first 20 plus a link to the Scryfall search.
