"""Health + configuration endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from apps.api.engine_cache import DATASET_OPTIONS, GPU_LEVELS
from apps.api.models import (
    DatasetSize,
    DatasetSizesResponse,
    GpuLevelResponse,
    HealthResponse,
)

router = APIRouter(tags=["config"])


@router.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Liveness probe."""
    return HealthResponse()


@router.get("/api/dataset/sizes", response_model=DatasetSizesResponse)
async def dataset_sizes() -> DatasetSizesResponse:
    """List available dataset sizes for the demo."""
    return DatasetSizesResponse(
        options=[
            DatasetSize(label=label, size=size) for label, size in DATASET_OPTIONS
        ],
    )


@router.get("/api/gpu/levels", response_model=GpuLevelResponse)
async def gpu_levels() -> GpuLevelResponse:
    """List available GPU levels (animation speed multipliers)."""
    return GpuLevelResponse(levels=list(GPU_LEVELS))
