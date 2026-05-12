"""Main conversational endpoint.

Accepts a list of messages, runs the guardrails, then hands off to the
Claude service for a tool-use loop. Returns the final assistant text plus
any cards that were referenced so the UI can render a card grid.
"""

from fastapi import APIRouter, HTTPException

from app.models.chat import ChatRequest, ChatResponse
from app.services import claude, guardrails

router = APIRouter()


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    # Refuse off-topic prompts up front so we don't pay for an LLM round-trip.
    refusal = guardrails.check_inbound(request.messages)
    if refusal is not None:
        return ChatResponse(reply=refusal, cards=[], stop_reason="refused")

    try:
        return await claude.run_conversation(request)
    except claude.ClaudeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
