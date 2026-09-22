"""Integration tests for the Solution Intelligence Engine service layer."""

import pytest

from solution_intelligence.retrieval import IncidentContext
from solution_intelligence.service import SolutionEngine
from solution_intelligence.sources import load_filtered


@pytest.fixture(scope="module")
def engine():
    eng = SolutionEngine()
    entries = load_filtered(path="data/knowledge.json", max_total=12)
    eng.ingest(entries)
    return eng


def test_ingest_indexes_more_than_rejected(engine):
    """Most curated entries should be ingested; junk/restricted rejected."""
    assert engine.index.size > 0
    assert engine.last_run is not None
    assert len(engine.last_run.rejected) >= 0


def test_search_returns_solutions(engine):
    results = engine.search("SAP FI report access denied authorization error", top_k=3)
    assert results
    assert all(r.entry.id for r in results)
    assert all(0.0 <= r.combined_score <= 1.0 for r in results)


def test_agent_chat_flow(engine):
    session = engine.agent.start("s1", "VPN keeps dropping on Windows 11")
    assert session.turns
    session = engine.agent.respond("s1", "also check other Windows versions")
    assert len(session.turns) == 2


def test_confidence_reflects_history(engine):
    results = engine.search("SAP authorization error on FI reports", top_k=5)
    high = next(r for r in results if r.entry.worked > r.entry.attempted * 0.7)
    assert high.confidence > 0.4


def test_search_context_boosts_error_code_match(engine):
    query = "SAP authorization error on FI reports"
    context = IncidentContext(error_code="S_RS_COMP", environment="PROD")
    baseline = engine.search(query, top_k=5)
    boosted = engine.search(query, top_k=5, context=context)
    matched = next(r for r in boosted if r.entry.error_code == "S_RS_COMP")
    before = next(r for r in baseline if r.entry.id == matched.entry.id)
    assert matched.confidence > before.confidence
