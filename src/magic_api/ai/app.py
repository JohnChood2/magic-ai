"""AI service: Claude tool-use chat (default port 8001)."""

from __future__ import annotations

import os

import uvicorn
from fastapi import FastAPI, HTTPException

from magic_api import __version__
from magic_api.ai import claude
from magic_api.utils.config import get_config
from magic_api.utils.models import ChatRequest, ChatResponse, HealthResponse

SERVICE = "ai"

app = FastAPI(
    title="MagicGPT AI API",
    version=__version__,
    description=(
        "Runs the Claude tool-use loop that answers Magic: The Gathering "
        "questions using Scryfall card data (fetched through the backend). "
        "Requires the `ANTHROPIC_API_KEY` environment variable."
    ),
    openapi_tags=[
        {"name": "meta", "description": "Liveness and service info."},
        {"name": "chat", "description": "LLM conversation."},
    ],
)


@app.get("/health", response_model=HealthResponse, tags=["meta"], summary="Liveness check")
def health() -> HealthResponse:
    """Reports the configured model and whether an API key is present."""
    return HealthResponse(
        service=SERVICE,
        version=__version__,
        details={
            "model": get_config().ai.model,
            "api_key_configured": bool(os.environ.get("ANTHROPIC_API_KEY")),
        },
    )


@app.post(
    "/chat",
    response_model=ChatResponse,
    tags=["chat"],
    summary="Run a chat turn",
    description=(
        "Runs a bounded tool-use loop (see `ai.max_turns` in config.yaml) and "
        "returns the final assistant text plus every card surfaced along the way."
    ),
    responses={502: {"description": "Anthropic call failed or API key is missing."}},
)
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        return await claude.run_conversation(request)
    except claude.ClaudeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


def main() -> None:
    cfg = get_config().ai
    uvicorn.run(app, host=cfg.host, port=cfg.port)


if __name__ == "__main__":
    main()
