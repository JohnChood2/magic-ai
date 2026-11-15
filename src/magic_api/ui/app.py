"""UI service: serves the chat web page (default port 8080).

The page talks directly to the backend API; `/config.json` tells it where
the backend lives, so the URL is defined only in config.yaml.
"""

from __future__ import annotations

from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from magic_api import __version__
from magic_api.utils.config import get_config, service_url
from magic_api.utils.models import HealthResponse

SERVICE = "ui"
STATIC_DIR = Path(__file__).parent / "static"


class ClientConfig(BaseModel):
    backend_url: str


app = FastAPI(
    title="MagicGPT UI",
    version=__version__,
    description=(
        "Serves the MagicGPT single-page chat UI. Unofficial fan content "
        "under Wizards of the Coast's Fan Content Policy."
    ),
    openapi_tags=[
        {"name": "meta", "description": "Liveness and service info."},
        {"name": "pages", "description": "HTML pages and static assets."},
    ],
)


@app.get("/health", response_model=HealthResponse, tags=["meta"], summary="Liveness check")
def health() -> HealthResponse:
    return HealthResponse(service=SERVICE, version=__version__)


@app.get(
    "/config.json",
    response_model=ClientConfig,
    tags=["meta"],
    summary="Browser runtime config",
    description="Where the page should send API calls. Derived from `backend` in config.yaml.",
)
def client_config() -> ClientConfig:
    return ClientConfig(backend_url=service_url("backend"))


@app.get(
    "/",
    include_in_schema=True,
    tags=["pages"],
    summary="Chat page",
    response_class=FileResponse,
    responses={200: {"content": {"text/html": {}}, "description": "The chat UI (index.html)."}},
)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html", media_type="text/html")


# Serves app.js, styles.css; mounted last so API routes win.
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def main() -> None:
    cfg = get_config().ui
    uvicorn.run(app, host=cfg.host, port=cfg.port)


if __name__ == "__main__":
    main()
