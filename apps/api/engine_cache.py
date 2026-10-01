"""The single shared engine behind the FastAPI app."""

from __future__ import annotations

from apps.api.demo_seed import seed_memory
from solution_intelligence.memory import ResolutionMemory
from solution_intelligence.service import SolutionEngine
from solution_intelligence.sources import load_filtered

GPU_LEVELS: list[str] = [
    "GPU Level 1 (Slow)",
    "GPU Level 2 (Medium)",
    "GPU Level 3 (Fast)",
]

_engine: SolutionEngine | None = None

# One shared Resolution Memory for the whole API process, persisted next to
# the dataset. On first use each process, the log is reset to the fixed demo
# seed (see apps.api.demo_seed) so every restart shows the same known
# learning state; outcomes recorded live during the session apply on top
# until the next restart.
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


def get_engine() -> SolutionEngine:
    """Return the shared engine, building it from the whole corpus on first call.

    There used to be one engine per ``max_entries`` so the sidebar could offer
    Debug (3) and Small (8) subsets. Those defaults were a development
    convenience and they were actively misleading: the app defaulted to 8
    records, which excluded the manufacturing AMS entries and nearly all of
    the multilingual coverage. One engine, the full corpus.
    """
    global _engine
    if _engine is None:
        engine = SolutionEngine(memory=_shared_memory())
        engine.ingest(load_filtered())
        _engine = engine
    return _engine


def reset_cache() -> None:
    """Drop all cached engines and swap in an in-memory-only Resolution
    Memory.

    Used by tests so they never touch the real on-disk outcome log nor the
    demo seed (the in-memory swap is never seeded); production never calls
    this, so it keeps the persistent, seeded default.
    """
    global _memory, _engine
    _engine = None
    _memory = ResolutionMemory(path=None)


def use_memory(memory: ResolutionMemory) -> None:
    """Point newly built engines at a specific ResolutionMemory (tests)."""
    reset_cache()
    global _memory
    _memory = memory
