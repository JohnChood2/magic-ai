"""Backend service: public API gateway (default port 8000).

* `/cards/search`        live Scryfall search
* `/cards/local/search`  search the local database service
* `/chat`                guardrails, then forwards to the AI service
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from magic_api import __version__
from magic_api.backend import guardrails, scryfall
from magic_api.utils.config import get_config, service_url
from magic_api.utils.models import (
    CardSearchResponse,
    ChatRequest,
    ChatResponse,
    HealthResponse,
)

SERVICE = "backend"
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logging.basicConfig(level=get_config().backend.log_level)
    yield
    await scryfall.close()


app = FastAPI(
    title="MagicGPT Backend API",
    version=__version__,
    description=(
        "Public API for the MagicGPT chatbot. Unofficial Magic: The Gathering "
        "card-search and Commander deck-building assistant; fan content under "
        "Wizards of the Coast's Fan Content Policy."
    ),
    openapi_tags=[
        {"name": "meta", "description": "Liveness and downstream status."},
        {"name": "chat", "description": "Conversational card search."},
        {"name": "cards", "description": "Direct card search."},
    ],
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[service_url("ui"), f"http://localhost:{get_config().ui.port}"],
    allow_methods=["*"],
    allow_headers=["*"],
)


async def _downstream_status(name: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(f"{service_url(name)}/health")  # type: ignore[arg-type]
        return "ok" if resp.status_code == 200 else f"http {resp.status_code}"
    except httpx.HTTPError:
        return "unreachable"


@app.get("/health", response_model=HealthResponse, tags=["meta"], summary="Liveness check")
async def health() -> HealthResponse:
    """Reports this service plus the reachability of the `ai` and `database` services."""
    return HealthResponse(
        service=SERVICE,
        version=__version__,
        details={"ai": await _downstream_status("ai"), "database": await _downstream_status("database")},
    )


@app.post(
    "/chat",
    response_model=ChatResponse,
    tags=["chat"],
    summary="Send a conversation to MagicGPT",
    responses={502: {"description": "The AI service failed or is unreachable."}},
)
async def chat(request: ChatRequest) -> ChatResponse:
    """Off-topic prompts (medical, legal, financial, relationship) are refused
    immediately without calling the LLM. Everything else is forwarded to the
    AI service, which runs the Claude tool-use loop against Scryfall."""
    refusal = guardrails.check_inbound(request.messages)
    if refusal is not None:
        return ChatResponse(reply=refusal, cards=[], stop_reason="refused")
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
            resp = await client.post(
                f"{service_url('ai')}/chat", json=request.model_dump(mode="json")
            )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"AI service unreachable: {exc}") from exc
    if resp.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"AI service error: {resp.text[:300]}")
    return ChatResponse.model_validate(resp.json())


@app.get(
    "/cards/search",
    response_model=CardSearchResponse,
    tags=["cards"],
    summary="Search cards on Scryfall",
    responses={502: {"description": "Scryfall returned an error."}},
)
async def search_cards(
    q: str = Query(..., description="Scryfall search syntax, e.g. `c:u t:creature`."),
    page: int = Query(1, ge=1, le=100),
    unique: str = Query("cards", description="`cards`, `art` or `prints`."),
) -> CardSearchResponse:
    try:
        return await scryfall.search(query=q, page=page, unique=unique)
    except scryfall.ScryfallError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@app.get(
    "/cards/local/search",
    response_model=CardSearchResponse,
    tags=["cards"],
    summary="Search cards in the local database",
    description="Proxies to the database service's `/cards/search` with the same filters.",
    responses={502: {"description": "Database service unreachable."}},
)
async def search_local_cards(
    name: str | None = Query(None, description="Substring of the card name."),
    type_line: str | None = Query(None, description="Substring of the type line."),
    text: str | None = Query(None, description="Substring of the Oracle text."),
    colors: str | None = Query(None, description="Required colors, e.g. `UB`."),
    cmc_max: float | None = Query(None, ge=0),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> CardSearchResponse:
    params = {
        k: v
        for k, v in dict(
            name=name, type_line=type_line, text=text, colors=colors,
            cmc_max=cmc_max, limit=limit, offset=offset,
        ).items()
        if v is not None
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{service_url('database')}/cards/search", params=params)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Database service error: {exc}") from exc
    return CardSearchResponse.model_validate(resp.json())


def main() -> None:
    cfg = get_config().backend
    uvicorn.run(app, host=cfg.host, port=cfg.port)


if __name__ == "__main__":
    main()
