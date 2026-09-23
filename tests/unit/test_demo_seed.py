"""Tests for the deterministic demo seed on Resolution Memory."""

from __future__ import annotations

from datetime import datetime, timezone

from apps.api import engine_cache
from apps.api.demo_seed import SEED_OUTCOMES, seed_memory
from solution_intelligence.memory import ResolutionMemory

# Every record the demo script quotes must stay untouched by the seed, or a
# scripted ranking / track-record beat breaks.
PROTECTED_DEMO_IDS = {
    "TIC-1001",  # voiceover: "worked 8 out of 8"
    "TIC-1004",  # CO auth near-duplicate beat
    "TIC-1008",  # VPN top hit
    "TIC-1009",
    "TIC-1010",
    "TIC-1011",  # VPN siblings
    "TIC-1013",  # account-lockout multilingual beat
    "TIC-1031",  # chat batch-job beat
    "KB_-1037",  # chat onboarding KB beat
    "TIC-1047",
    "TIC-1048",  # honest-gap nearest look-alikes
    "TIC-3011",
    "TIC-3012",  # M8149 context-trap pair
}


def test_seed_writes_all_outcomes_and_expected_split():
    memory = ResolutionMemory(path=None)
    written = seed_memory(memory)
    assert written == len(SEED_OUTCOMES)
    stats = memory.stats()
    assert stats["total"] == 14
    assert stats["worked"] == 11
    assert stats["rejected"] == 3
    assert stats["success_rate"] == 0.786
    assert stats["entries_learned"] == 14


def test_seed_uses_one_outcome_per_distinct_entry():
    memory = ResolutionMemory(path=None)
    seed_memory(memory)
    assert set(memory.entry_deltas()) == {row[0] for row in SEED_OUTCOMES}


def test_seed_never_touches_protected_demo_records():
    seeded = {row[0] for row in SEED_OUTCOMES}
    assert not seeded & PROTECTED_DEMO_IDS


def test_seed_newest_record_is_recent_and_last():
    """Recency is computed at seed time; the last record is the newest."""
    memory = ResolutionMemory(path=None)
    seed_memory(memory)
    last_outcome_at = memory.stats()["last_outcome_at"]
    assert last_outcome_at
    age = datetime.now(timezone.utc) - datetime.fromisoformat(last_outcome_at)
    assert 0 <= age.total_seconds() < 3600  # newest within the last hour


def test_seed_resets_existing_records():
    """Restarting reseeds: prior-session outcomes are wiped, not appended."""
    memory = ResolutionMemory(path=None)
    memory.record("STALE", False, source="ui")
    memory.record("STALE", True, source="ui")
    seed_memory(memory)
    assert len(memory) == len(SEED_OUTCOMES)
    assert set(memory.entry_deltas()) == {row[0] for row in SEED_OUTCOMES}


def test_shared_memory_seeds_on_first_process_use(monkeypatch):
    """The first build per process resets to the demo seed (restart reseed)."""
    fake = ResolutionMemory(path=None)
    monkeypatch.setattr(engine_cache, "ResolutionMemory", lambda: fake)
    monkeypatch.setattr(engine_cache, "_memory", None)
    monkeypatch.setattr(engine_cache, "_engine_cache", {})
    memory = engine_cache._shared_memory()
    assert memory is fake
    assert len(memory) == len(SEED_OUTCOMES)


def test_reset_cache_yields_unseeded_memory():
    """Tests swap to an in-memory memory that is never seeded."""
    engine_cache.reset_cache()
    assert len(engine_cache._shared_memory()) == 0
