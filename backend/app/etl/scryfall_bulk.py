"""Skeleton ETL for Scryfall bulk data.

Phase 1 of the project doesn't strictly need a local card index — the live
Scryfall /cards/search API is fast and free. But the README anticipates a
local DB eventually (for vector search over Oracle text, custom tagging,
EDHREC-style aggregations, etc.), so this script is the entry point.

Usage:
    python -m app.etl.scryfall_bulk --type oracle_cards --out ./data/oracle.json

What it does (intentionally minimal):
  1. Hits /bulk-data, picks the requested bulk export.
  2. Streams the download to disk.
  3. (TODO) Loads it into your DB of choice — Postgres + pgvector, SQLite,
     LanceDB, etc. We don't pick one yet; add a loader when you do.

Scryfall bulk data is regenerated daily; running this as a nightly cron is
the typical pattern.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

# Documented bulk-data types: https://scryfall.com/docs/api/bulk-data
KNOWN_BULK_TYPES = {
    "oracle_cards",     # one printing per unique card, recommended for search
    "unique_artwork",   # one printing per artwork variant
    "default_cards",    # every printing
    "all_cards",        # every printing including non-English
    "rulings",          # all card rulings
}


async def _fetch_bulk_metadata(client: httpx.AsyncClient, bulk_type: str) -> dict:
    resp = await client.get("/bulk-data")
    resp.raise_for_status()
    data = resp.json().get("data", [])
    for entry in data:
        if entry.get("type") == bulk_type:
            return entry
    raise RuntimeError(f"Bulk data type {bulk_type!r} not found in Scryfall response")


async def _stream_download(
    client: httpx.AsyncClient, url: str, out_path: Path
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    async with client.stream("GET", url) as resp:
        resp.raise_for_status()
        total = int(resp.headers.get("Content-Length", 0))
        written = 0
        with out_path.open("wb") as fp:
            async for chunk in resp.aiter_bytes(chunk_size=64 * 1024):
                fp.write(chunk)
                written += len(chunk)
                if total:
                    pct = (written / total) * 100
                    print(f"\r  {written / 1_000_000:.1f} MB  ({pct:.1f}%)", end="")
        print()


async def run(bulk_type: str, out_path: Path) -> None:
    if bulk_type not in KNOWN_BULK_TYPES:
        raise SystemExit(
            f"Unknown bulk type {bulk_type!r}. Known: {sorted(KNOWN_BULK_TYPES)}"
        )

    settings = get_settings()
    async with httpx.AsyncClient(
        base_url=settings.scryfall_api_base,
        headers={"User-Agent": settings.scryfall_user_agent},
        timeout=httpx.Timeout(60.0),
    ) as client:
        logger.info("Looking up Scryfall bulk metadata for %s", bulk_type)
        meta = await _fetch_bulk_metadata(client, bulk_type)
        download_uri = meta["download_uri"]
        updated_at = meta.get("updated_at")
        size = meta.get("size")
        logger.info(
            "Downloading %s (updated %s, %.1f MB) -> %s",
            bulk_type, updated_at, (size or 0) / 1_000_000, out_path,
        )
        await _stream_download(client, download_uri, out_path)
        logger.info("Done.")

    # TODO: replace this with a real loader when a DB is chosen.
    # e.g. read JSON lines, normalize via app.models.card.Card, upsert into
    # Postgres / SQLite / vector store of your choice.


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Download a Scryfall bulk-data dump.")
    p.add_argument(
        "--type",
        default="oracle_cards",
        help=f"Bulk type. One of: {sorted(KNOWN_BULK_TYPES)}",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=Path("./data/oracle_cards.json"),
        help="Destination path.",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = _parse_args(argv or sys.argv[1:])
    asyncio.run(run(args.type, args.out))


if __name__ == "__main__":
    main()
