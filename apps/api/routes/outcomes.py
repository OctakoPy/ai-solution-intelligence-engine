"""Confirmed-outcome write-back endpoint (Resolution Memory loop)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from apps.api.engine_cache import get_or_build_engine
from apps.api.models import OutcomeRequest, OutcomeResponse
from solution_intelligence.retrieval import IncidentContext as CoreContext

router = APIRouter(tags=["outcomes"])


@router.post("/api/outcomes", response_model=OutcomeResponse)
async def record_outcome(req: OutcomeRequest) -> OutcomeResponse:
    """Record a confirmed outcome and fold it back into future ranking."""
    engine = get_or_build_engine(0)
    context: CoreContext | None = (
        CoreContext(
            error_code=req.context.error_code,
            module=req.context.module,
            environment=req.context.environment,
        )
        if req.context
        else None
    )
    try:
        record = engine.record_outcome(
            req.entry_id,
            req.success,
            note=req.note,
            context=context,
            source="ui",
        )
    except KeyError:
        raise HTTPException(
            status_code=404, detail=f"unknown entry id: {req.entry_id!r}"
        ) from None
    entry = engine.index.get(record.entry_id)
    assert entry is not None  # record_outcome validated the id
    return OutcomeResponse(
        recorded=True,
        entry_id=record.entry_id,
        success=record.success,
        worked_count=[entry.worked, entry.attempted],
        total_outcomes=len(engine.memory),
    )


@router.get("/api/outcomes/status", response_model=OutcomeResponse)
async def outcome_status(entry_id: str) -> OutcomeResponse:
    """Return the learned outcome state for one entry (no write)."""
    engine = get_or_build_engine(0)
    entry = engine.index.get(entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"unknown entry id: {entry_id!r}")
    delta_worked, delta_attempted = engine.memory.entry_deltas().get(entry_id, (0, 0))
    return OutcomeResponse(
        recorded=False,
        entry_id=entry_id,
        success=bool(delta_attempted) and delta_worked > 0,
        worked_count=[entry.worked, entry.attempted],
        total_outcomes=delta_attempted,
    )
