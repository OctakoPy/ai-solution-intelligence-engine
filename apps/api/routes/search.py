"""Search endpoint backed by the engine's KnowledgeIndex."""

from __future__ import annotations

from fastapi import APIRouter

from apps.api.engine_cache import get_or_build_engine
from apps.api.models import RetrievedSolution, SearchRequest, SearchResponse
from apps.api.views import SOURCE_LABELS

router = APIRouter(tags=["search"])


@router.post("/api/search", response_model=SearchResponse)
async def search(req: SearchRequest) -> SearchResponse:
    """Free-text search across the indexed knowledge base."""
    engine = get_or_build_engine(0)
    hits = engine.search(req.query, top_k=req.top_k)
    payload = [
        RetrievedSolution(
            id=h.entry.id,
            title=h.entry.title,
            source=SOURCE_LABELS.get(h.entry.source_type, h.entry.source_type),
            category=h.entry.category,
            score=round(h.combined_score, 3),
            confidence=round(h.confidence, 3),
            description=h.entry.description,
            resolution=h.entry.resolution,
            date=h.entry.date or "\u2014",
            language=h.entry.language or "en",
            english_title=h.entry.english_title,
            english_description=h.entry.english_description,
            english_resolution=h.entry.english_resolution,
        )
        for h in hits
    ]
    return SearchResponse(results=payload)
