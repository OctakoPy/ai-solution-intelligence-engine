"""Ingestion + pipeline views endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from apps.api.engine_cache import get_engine
from apps.api.models import IngestResponse, View
from apps.api.views import build_views

router = APIRouter(tags=["pipeline"])


@router.post("/api/ingest", response_model=IngestResponse)
async def ingest() -> IngestResponse:
    """Ensure the engine has ingested the corpus, then report the run.

    Takes no request body. The route used to require one carrying
    ``max_entries``; when that field was removed the model was left behind as
    an empty-but-required body, so the frontend's bodyless POST returned 422
    and the Pipeline page never received its views.
    """
    engine = get_engine()
    run = engine.last_run
    if run is None:
        raise HTTPException(status_code=500, detail="ingestion produced no run")
    return IngestResponse(
        ingested=len(run.ingested),
        rejected=len(run.rejected),
        total=len(run.ingested) + len(run.rejected),
    )


@router.get("/api/pipeline/views", response_model=list[View])
async def pipeline_views() -> list[View]:
    """Return per-record views ready for the playback animation."""
    engine = get_engine()
    run = engine.last_run
    if run is None:
        raise HTTPException(status_code=500, detail="ingestion produced no run")
    return [View(**v) for v in build_views(run)]
