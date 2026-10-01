"""Health + configuration endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from apps.api.engine_cache import GPU_LEVELS
from apps.api.models import GpuLevelResponse, HealthResponse

router = APIRouter(tags=["config"])


@router.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Liveness probe."""
    return HealthResponse()


@router.get("/api/gpu/levels", response_model=GpuLevelResponse)
async def gpu_levels() -> GpuLevelResponse:
    """List available GPU levels (animation speed multipliers)."""
    return GpuLevelResponse(levels=list(GPU_LEVELS))
