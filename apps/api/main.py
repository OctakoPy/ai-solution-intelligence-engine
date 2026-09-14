"""Solution Intelligence Engine — FastAPI entry point."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from apps.api.routes import analytics, chat, config, overview, pipeline, search

app = FastAPI(
    title="Solution Intelligence Engine API",
    version="0.10.0",
    description=(
        "Backend for the Solution Intelligence Engine demo. Wraps the "
        "`solution_intelligence` package behind a JSON HTTP surface."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5179",
        "http://127.0.0.1:5179",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(config.router)
app.include_router(pipeline.router)
app.include_router(analytics.router)
app.include_router(search.router)
app.include_router(chat.router)
app.include_router(overview.router)

_DIST = Path(__file__).resolve().parents[2] / "apps" / "web" / "dist"
if _DIST.exists():
    app.mount("/", StaticFiles(directory=_DIST, html=True), name="web")


def create_app() -> FastAPI:
    """Application factory (used by tests)."""
    return app
