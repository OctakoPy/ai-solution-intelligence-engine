"""Search endpoint backed by the engine's KnowledgeIndex."""

from __future__ import annotations

from fastapi import APIRouter

from apps.api.engine_cache import get_or_build_engine
from apps.api.models import (
    IncidentContext,
    RetrievedSolution,
    SearchRequest,
    SearchResponse,
)
from apps.api.views import SOURCE_LABELS
from solution_intelligence.retrieval import IncidentContext as CoreContext
from solution_intelligence.retrieval import matched_signals

router = APIRouter(tags=["search"])


def _to_context(req: IncidentContext | None) -> CoreContext | None:
    """Convert a request context into the engine's core context model."""
    if req is None:
        return None
    return CoreContext(
        error_code=req.error_code,
        module=req.module,
        environment=req.environment,
    )


@router.post("/api/search", response_model=SearchResponse)
async def search(req: SearchRequest) -> SearchResponse:
    """Free-text search across the indexed knowledge base."""
    engine = get_or_build_engine(0)
    context = _to_context(req.context)
    hits = engine.search(req.query, top_k=req.top_k, context=context)
    payload = [
        RetrievedSolution(
            id=h.entry.id,
            title=h.entry.title,
            source=SOURCE_LABELS.get(h.entry.source_type, h.entry.source_type),
            category=h.entry.category,
            score=round(h.confidence, 3),
            confidence=round(h.confidence, 3),
            description=h.entry.description,
            resolution=h.entry.resolution,
            date=h.entry.date or "\u2014",
            language=h.entry.language or "en",
            english_title=h.entry.english_title,
            english_description=h.entry.english_description,
            english_resolution=h.entry.english_resolution,
            signals=matched_signals(h.entry, context),
        )
        for h in hits
    ]
    return SearchResponse(results=payload)
