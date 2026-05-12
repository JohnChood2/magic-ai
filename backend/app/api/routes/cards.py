"""Thin Scryfall pass-through endpoints.

These exist so the frontend can render card grids/hover-images without
re-implementing Scryfall search syntax. The chat endpoint does the heavy
lifting via Claude tool-use; this is the direct-search escape hatch.
"""

from fastapi import APIRouter, HTTPException, Query

from app.models.card import CardSearchResponse
from app.services import scryfall

router = APIRouter()


@router.get("/search", response_model=CardSearchResponse)
async def search_cards(
    q: str = Query(..., description="Scryfall search syntax, e.g. 'c:u t:creature'"),
    page: int = Query(1, ge=1, le=100),
    unique: str = Query("cards", description="cards | art | prints"),
) -> CardSearchResponse:
    try:
        return await scryfall.search(query=q, page=page, unique=unique)
    except scryfall.ScryfallError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
