"""Per-`max_entries` engine cache shared by the FastAPI app."""

from __future__ import annotations

from apps.api.demo_seed import seed_memory
from solution_intelligence.memory import ResolutionMemory
from solution_intelligence.service import SolutionEngine
from solution_intelligence.sources import load_filtered

DATASET_OPTIONS: list[tuple[str, int]] = [
    ("Debug (3)", 3),
    ("Small (8)", 8),
    ("Full (78)", 78),
]

GPU_LEVELS: list[str] = [
    "GPU Level 1 (Slow)",
    "GPU Level 2 (Medium)",
    "GPU Level 3 (Fast)",
]

_engine_cache: dict[int, SolutionEngine] = {}

# One shared Resolution Memory for the whole API process, persisted next to
# the dataset. On first use each process, the log is reset to the fixed demo
# seed (see apps.api.demo_seed) so every restart shows the same known
# learning state; outcomes recorded live during the session apply on top
# until the next restart. Learning is per knowledge record, not per cache
# key, so the shared memory applies to every engine variant.
_memory: ResolutionMemory | None = None


def _shared_memory() -> ResolutionMemory:
    """Lazily build the process-wide Resolution Memory.

    The first build per process resets the log to the fixed demo seed, so
    every API restart starts from the same known learning state.
    """
    global _memory
    if _memory is None:
        _memory = ResolutionMemory()
        seed_memory(_memory)
    return _memory


def get_or_build_engine(max_entries: int) -> SolutionEngine:
    """Return a cached engine for `max_entries`, building it on first call.

    ``max_entries`` <= 0 (or a large sentinel) loads the entire dataset so
    every record — including multilingual entries — is searchable.
    """
    key = max_entries if max_entries > 0 else -1
    if key not in _engine_cache:
        engine = SolutionEngine(memory=_shared_memory())
        entries = load_filtered(max_total=max_entries)
        engine.ingest(entries)
        _engine_cache[key] = engine
    return _engine_cache[key]


def reset_cache() -> None:
    """Drop all cached engines and swap in an in-memory-only Resolution
    Memory.

    Used by tests so they never touch the real on-disk outcome log nor the
    demo seed (the in-memory swap is never seeded); production never calls
    this, so it keeps the persistent, seeded default.
    """
    global _memory
    _engine_cache.clear()
    _memory = ResolutionMemory(path=None)


def use_memory(memory: ResolutionMemory) -> None:
    """Point newly built engines at a specific ResolutionMemory (tests)."""
    reset_cache()
    global _memory
    _memory = memory
