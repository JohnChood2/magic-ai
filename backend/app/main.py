"""FastAPI application factory.

Kept small on purpose — wire routes/middleware here, business logic lives in
`app.services` and `app.api.routes`.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.routes import cards, chat, health
from app.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level)

    app = FastAPI(
        title="MagicGPT API",
        version=__version__,
        description=(
            "Unofficial MTG card-search and Commander deck-building chatbot. "
            "Fan content under Wizards of the Coast's Fan Content Policy."
        ),
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, tags=["meta"])
    app.include_router(chat.router, prefix="/chat", tags=["chat"])
    app.include_router(cards.router, prefix="/cards", tags=["cards"])

    return app


app = create_app()
