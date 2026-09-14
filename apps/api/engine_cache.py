"""Per-`max_entries` engine cache shared by the FastAPI app."""

from __future__ import annotations

from typing import TYPE_CHECKING

from solution_intelligence.service import SolutionEngine
from solution_intelligence.sources import load_filtered

if TYPE_CHECKING:
    pass

DATASET_OPTIONS: list[tuple[str, int]] = [
    ("Debug (3)", 3),
    ("Small (8)", 8),
    ("Full (76)", 76),
]

GPU_LEVELS: list[str] = [
    "GPU Level 1 (Slow)",
    "GPU Level 2 (Medium)",
    "GPU Level 3 (Fast)",
]

_engine_cache: dict[int, SolutionEngine] = {}


def get_or_build_engine(max_entries: int) -> SolutionEngine:
    """Return a cached engine for `max_entries`, building it on first call.

    ``max_entries`` <= 0 (or a large sentinel) loads the entire dataset so
    every record — including multilingual entries — is searchable.
    """
    key = max_entries if max_entries > 0 else -1
    if key not in _engine_cache:
        engine = SolutionEngine()
        entries = load_filtered(max_total=max_entries)
        engine.ingest(entries)
        _engine_cache[key] = engine
    return _engine_cache[key]


def reset_cache() -> None:
    """Drop all cached engines (used by tests)."""
    _engine_cache.clear()
