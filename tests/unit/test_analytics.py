"""Unit tests for dashboard analytics helpers."""

from __future__ import annotations

from solution_intelligence.analytics import proven_fixes
from solution_intelligence.models import KnowledgeEntry


def _entry(entry_id: str, worked: tuple[int, int]) -> KnowledgeEntry:
    """Build a minimal entry with a given track record."""
    return KnowledgeEntry(
        id=entry_id,
        source_type="ticket",
        title=f"Record {entry_id}",
        description="A recurring enterprise issue with a known fix.",
        worked_count=worked,
    )


def test_proven_fixes_counts_perfect_track_records():
    entries = [
        _entry("P1", (5, 5)),  # proven: enough attempts, never failed
        _entry("P2", (3, 3)),  # proven: exactly at the attempt minimum
        _entry("F1", (2, 4)),  # not proven: failed at least once
        _entry("S1", (1, 1)),  # not proven: perfect but too few attempts
        _entry("N1", (0, 0)),  # not proven: no track record yet
    ]
    assert proven_fixes(entries) == 2


def test_proven_fixes_empty_index_is_zero():
    assert proven_fixes([]) == 0
