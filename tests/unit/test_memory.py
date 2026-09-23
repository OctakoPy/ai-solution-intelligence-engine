"""Tests for Resolution Memory: confirmed-outcome write-back (issue #16)."""

from __future__ import annotations

import pytest

from solution_intelligence.memory import OutcomeRecord, ResolutionMemory
from solution_intelligence.models import KnowledgeEntry
from solution_intelligence.retrieval import IncidentContext
from solution_intelligence.service import SolutionEngine


def make_entry(
    entry_id: str,
    title: str,
    *,
    worked=(3, 3),
    error_code: str | None = None,
    module: str | None = None,
    environment: str | None = None,
) -> KnowledgeEntry:
    """Build a minimal indexed entry for memory tests."""
    return KnowledgeEntry(
        id=entry_id,
        source_type="ticket",
        title=title,
        description=f"Description for {title}",
        resolution="Applied the standard fix and confirmed it works.",
        category="sap_authorization",
        date="2025-01-01",
        worked_count=worked,
        error_code=error_code,
        module=module,
        environment=environment,
    )


# --- OutcomeRecord serialisation ---------------------------------------------


def test_outcome_record_roundtrip():
    record = OutcomeRecord(
        entry_id="TIC-1",
        success=True,
        note="fixed it",
        error_code="M8149",
        module="SAP MM",
        environment="PROD",
        timestamp="2026-09-22T10:00:00+00:00",
        source="ui",
    )
    rebuilt = OutcomeRecord.from_dict(record.to_dict())
    assert rebuilt == record


# --- Deltas and idempotent application ---------------------------------------


def test_entry_deltas_count_successes_and_failures():
    memory = ResolutionMemory(path=None)
    memory.record("A", True, source="test")
    memory.record("A", True, source="test")
    memory.record("A", False, source="test")
    memory.record("B", False, source="test")
    deltas = memory.entry_deltas()
    assert deltas["A"] == (2, 3)
    assert deltas["B"] == (0, 1)


def test_apply_is_idempotent_across_reingestion():
    """Applying to a re-ingested copy never double-counts."""
    memory = ResolutionMemory(path=None)
    memory.record("T1", True, source="test")
    memory.record("T1", False, source="test")

    first = make_entry("T1", "VPN drops", worked=(4, 4))
    memory.apply([first])
    assert first.worked_count == (5, 6)

    # A fresh in-memory copy of the same record (what re-ingestion builds).
    second = make_entry("T1", "VPN drops", worked=(4, 4))
    memory.apply([second])
    assert second.worked_count == (5, 6), "base must be captured, not mutated"


def test_apply_only_touches_entries_with_outcomes():
    memory = ResolutionMemory(path=None)
    memory.record("HAS", True, source="test")
    touched = make_entry("HAS", "t", worked=(1, 2))
    untouched = make_entry("OTHER", "t", worked=(7, 7))
    adjusted = memory.apply([touched, untouched])
    assert adjusted == 1
    assert untouched.worked_count == (7, 7)
    assert touched.worked_count == (2, 3)


def test_deleting_the_log_resets_learning(tmp_path):
    """The JSON log is the single source of learned state."""
    log = tmp_path / "memory.json"
    memory = ResolutionMemory(path=log)
    memory.record("T1", True, source="test")
    assert log.exists()

    fresh = ResolutionMemory(path=log)
    assert len(fresh) == 1
    log.unlink()
    assert len(ResolutionMemory(path=log)) == 0


def test_malformed_log_raises(tmp_path):
    log = tmp_path / "memory.json"
    log.write_text('{"not": "a list"}', encoding="utf-8")
    with pytest.raises(ValueError):
        ResolutionMemory(path=log)


def test_clear_empties_and_persists(tmp_path):
    """clear() wipes the log in memory and on disk."""
    log = tmp_path / "memory.json"
    memory = ResolutionMemory(path=log)
    memory.record("T1", True, source="test")
    assert len(memory) == 1

    memory.clear()
    assert len(memory) == 0
    assert memory.stats()["total"] == 0
    assert len(ResolutionMemory(path=log)) == 0


def test_record_accepts_explicit_timestamp():
    """An explicit timestamp overrides the clock (used by the demo seed)."""
    memory = ResolutionMemory(path=None)
    memory.record("T1", True, source="ui", timestamp="2026-09-20T09:00:00+00:00")
    stats = memory.stats()
    assert stats["last_outcome_at"] == "2026-09-20T09:00:00+00:00"


# --- Dashboard stats ----------------------------------------------------------


def test_stats_empty_memory_reports_honest_zeros():
    """An untouched memory reports zeros, never fabricated numbers."""
    stats = ResolutionMemory(path=None).stats()
    assert stats == {
        "total": 0,
        "worked": 0,
        "rejected": 0,
        "success_rate": 0.0,
        "entries_learned": 0,
        "last_outcome_at": None,
    }


def test_stats_aggregates_confirmed_outcomes():
    memory = ResolutionMemory(path=None)
    memory.record("A", True, source="test")
    memory.record("A", True, source="test")
    memory.record("A", False, source="test")
    memory.record("B", False, source="test")
    stats = memory.stats()
    assert stats["total"] == 4
    assert stats["worked"] == 2
    assert stats["rejected"] == 2
    assert stats["success_rate"] == 0.5
    assert stats["entries_learned"] == 2
    assert stats["last_outcome_at"]  # set at record time


# --- Engine integration: the learning loop ------------------------------------


@pytest.fixture(scope="module")
def engine():
    """Engine over a tiny synthetic dataset (cached-embedding texts only)."""
    eng = SolutionEngine()  # default memory is in-memory-only
    eng.ingest(
        [
            make_entry(
                "VPN-FIX",
                "VPN keeps dropping after five minutes",
                worked=(4, 4),
            ),
            make_entry(
                "PRINTER-FIX",
                "Printer is jammed and needs new toner",
                worked=(2, 4),
            ),
        ],
        collect_steps=False,
    )
    return eng


def test_record_outcome_unknown_id_raises(engine):
    with pytest.raises(KeyError):
        engine.record_outcome("NOPE", success=True)


def test_confirmed_failure_demotes_candidate(engine):
    """Negative learning: a failed outcome must lower the next confidence."""
    query = "vpn keeps dropping after a few minutes"
    before = next(r for r in engine.search(query, top_k=5) if r.entry.id == "VPN-FIX")
    before_confidence = before.confidence
    base_worked = before.entry.worked
    base_attempted = before.entry.attempted
    engine.record_outcome("VPN-FIX", success=False, source="test")
    after = next(r for r in engine.search(query, top_k=5) if r.entry.id == "VPN-FIX")
    assert after.confidence < before_confidence
    assert after.entry.worked == base_worked
    assert after.entry.attempted == base_attempted + 1


def test_confirmed_success_boosts_candidate(engine):
    """Positive learning: a confirmed outcome raises the success signal."""
    query = "printer is jammed"
    before = next(
        r for r in engine.search(query, top_k=5) if r.entry.id == "PRINTER-FIX"
    )
    before_confidence = before.confidence
    base_worked = before.entry.worked
    base_attempted = before.entry.attempted
    engine.record_outcome("PRINTER-FIX", success=True, source="test")
    after = next(
        r for r in engine.search(query, top_k=5) if r.entry.id == "PRINTER-FIX"
    )
    assert after.confidence > before_confidence
    assert after.entry.worked == base_worked + 1
    assert after.entry.attempted == base_attempted + 1


def test_outcome_with_context_is_captured(engine):
    record = engine.record_outcome(
        "VPN-FIX",
        success=True,
        note="recreated profile",
        context=IncidentContext(error_code="VPN404", environment="PROD"),
        source="test",
    )
    assert record.error_code == "VPN404"
    assert record.environment == "PROD"
    assert record.note == "recreated profile"


def test_learning_survives_reingestion(engine):
    """Repeated applies (re-ingestion) never change the learned counts."""
    vpn = engine.index.get("VPN-FIX")
    assert vpn is not None
    learned = vpn.worked_count
    engine.ingest(
        [make_entry("EXTRA", "A brand new unique issue to index")],
        collect_steps=False,
    )
    vpn_after = engine.index.get("VPN-FIX")
    assert vpn_after is not None
    assert vpn_after.worked_count == learned
