"""Database service: SQLite-backed card store (default port 8002).

Holds cards loaded from Scryfall bulk data (see README Phase 1 ETL) and
serves local search so the backend does not have to hit Scryfall every time.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from magic_api import __version__
from magic_api.utils.config import get_config, sqlite_path
from magic_api.utils.models import Card, CardSearchResponse, HealthResponse

SERVICE = "database"

SCHEMA = """
CREATE TABLE IF NOT EXISTS cards (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type_line TEXT,
    oracle_text TEXT,
    colors TEXT,
    color_identity TEXT,
    cmc REAL,
    data TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cards_name ON cards(name);
"""


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    path = sqlite_path(get_config().database.database_url)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        conn.executescript(SCHEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()


class UpsertResult(BaseModel):
    upserted: int


app = FastAPI(
    title="MagicGPT Database API",
    version=__version__,
    description=(
        "SQLite-backed store of Magic: The Gathering cards. Unofficial fan "
        "content under Wizards of the Coast's Fan Content Policy."
    ),
    openapi_tags=[
        {"name": "meta", "description": "Liveness and service info."},
        {"name": "cards", "description": "Store, fetch and search cards."},
    ],
)


@app.get("/health", response_model=HealthResponse, tags=["meta"], summary="Liveness check")
def health() -> HealthResponse:
    """Returns `ok` plus the number of cards currently stored."""
    with connect() as conn:
        count = conn.execute("SELECT COUNT(*) FROM cards").fetchone()[0]
    return HealthResponse(service=SERVICE, version=__version__, details={"cards": count})


@app.put(
    "/cards",
    response_model=UpsertResult,
    tags=["cards"],
    summary="Bulk upsert cards",
    description="Insert or replace cards by `id`. Used by the Scryfall bulk ETL.",
)
def upsert_cards(cards: list[Card]) -> UpsertResult:
    rows = [
        (
            c.id,
            c.name,
            c.type_line,
            c.oracle_text,
            json.dumps(c.colors or []),
            json.dumps(c.color_identity or []),
            c.cmc,
            c.model_dump_json(),
        )
        for c in cards
    ]
    with connect() as conn:
        conn.executemany(
            "INSERT OR REPLACE INTO cards "
            "(id, name, type_line, oracle_text, colors, color_identity, cmc, data) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            rows,
        )
    return UpsertResult(upserted=len(rows))


@app.get(
    "/cards/search",
    response_model=CardSearchResponse,
    tags=["cards"],
    summary="Search stored cards",
    description="All filters are optional and combined with AND. Text filters are case-insensitive substring matches.",
)
def search_cards(
    name: str | None = Query(None, description="Substring of the card name."),
    type_line: str | None = Query(None, description="Substring of the type line, e.g. `dragon`."),
    text: str | None = Query(None, description="Substring of the Oracle text."),
    colors: str | None = Query(
        None, description="Colors the card must include, e.g. `UB` (W, U, B, R, G)."
    ),
    cmc_max: float | None = Query(None, ge=0, description="Maximum mana value."),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> CardSearchResponse:
    where: list[str] = []
    params: list[object] = []
    for column, value in (("name", name), ("type_line", type_line), ("oracle_text", text)):
        if value:
            where.append(f"{column} LIKE ? ESCAPE '\\'")
            escaped = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            params.append(f"%{escaped}%")
    for color in (colors or "").upper():
        where.append("colors LIKE ?")
        params.append(f'%"{color}"%')
    if cmc_max is not None:
        where.append("cmc <= ?")
        params.append(cmc_max)
    clause = f"WHERE {' AND '.join(where)}" if where else ""

    with connect() as conn:
        total = conn.execute(f"SELECT COUNT(*) FROM cards {clause}", params).fetchone()[0]
        rows = conn.execute(
            f"SELECT data FROM cards {clause} ORDER BY name LIMIT ? OFFSET ?",
            [*params, limit, offset],
        ).fetchall()
    return CardSearchResponse(
        total_cards=total,
        has_more=offset + len(rows) < total,
        data=[Card.model_validate_json(r["data"]) for r in rows],
    )


@app.get(
    "/cards/{card_id}",
    response_model=Card,
    tags=["cards"],
    summary="Get a card by id",
    responses={404: {"description": "No card with that id."}},
)
def get_card(card_id: str) -> Card:
    with connect() as conn:
        row = conn.execute("SELECT data FROM cards WHERE id = ?", (card_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Card not found")
    return Card.model_validate_json(row["data"])


def main() -> None:
    cfg = get_config().database
    uvicorn.run(app, host=cfg.host, port=cfg.port)


if __name__ == "__main__":
    main()
