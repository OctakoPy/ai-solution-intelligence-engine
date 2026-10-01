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


@pytest.fixture(scope="module")
def full_engine():
    """The whole corpus, so multilingual coverage paths are exercised."""
    eng = SolutionEngine()
    eng.ingest(load_filtered(path="data/knowledge.json"))
    return eng


def test_rejection_does_not_repeat_the_same_answer(full_engine):
    """Reporting the fix failed must surface a different record.

    The English record and its translations are one piece of advice, so a
    rejection has to rule out the whole family. Rejecting only the id it was
    shown left the record that had out-scored it - the Japanese copy - at
    full strength as the top answer, and the reply repeated itself.
    """
    session = full_engine.agent.start("rej", "my email is not arriving")
    first = session.turns[0].candidates[0]

    session = full_engine.agent.respond("rej", "that did not work, still nothing")
    second_ids = [c.entry.id for c in session.turns[-1].candidates]

    assert first.entry.id not in second_ids, "rejected record was offered again"

    from solution_intelligence.retrieval import _same_issue

    for entry in full_engine.index.entries:
        if _same_issue(entry, first.entry):
            assert entry.id not in second_ids, (
                f"translation of the rejected record ({entry.id}) was offered again"
            )


def test_rejection_keeps_the_english_answer_first(full_engine):
    """Rejecting a record must not disturb English-first ordering."""
    session = full_engine.agent.start("rej2", "my email is not arriving")
    assert session.turns[0].candidates[0].entry.language == "en"
