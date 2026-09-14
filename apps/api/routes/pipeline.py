"""Ingestion + pipeline views endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from apps.api.engine_cache import get_or_build_engine
from apps.api.models import IngestRequest, IngestResponse, View
from apps.api.views import build_views

router = APIRouter(tags=["pipeline"])


@router.post("/api/ingest", response_model=IngestResponse)
async def ingest(req: IngestRequest) -> IngestResponse:
    """Build the engine for `max_entries` and run ingestion if not cached."""
    engine = get_or_build_engine(req.max_entries)
    run = engine.last_run
    if run is None:
        raise HTTPException(status_code=500, detail="ingestion produced no run")
    return IngestResponse(
        ingested=len(run.ingested),
        rejected=len(run.rejected),
        total=len(run.ingested) + len(run.rejected),
    )


@router.get("/api/pipeline/views", response_model=list[View])
async def pipeline_views(max_entries: int = 8) -> list[View]:
    """Return per-record views ready for the playback animation."""
    engine = get_or_build_engine(max_entries)
    run = engine.last_run
    if run is None:
        raise HTTPException(status_code=500, detail="ingestion produced no run")
    return [View(**v) for v in build_views(run)]
