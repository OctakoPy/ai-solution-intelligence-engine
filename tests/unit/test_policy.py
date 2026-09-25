"""Tests for the shared abstain policy (issue #18).

The policy is the single source of truth for "knows when not to guess":
band thresholds, next-best-action payloads, and context-trap detection
must behave identically for Find, Chat, and the eval framework.
"""

import pytest

from solution_intelligence.models import KnowledgeEntry, RetrievedSolution
from solution_intelligence.policy import (
    ABSTAIN_THRESHOLD,
    CONFIDENT_THRESHOLD,
    PROVEN_FLOOR,
    PROVEN_MIN_ATTEMPTS,
    PolicyVerdict,
    decide,
    is_context_trap,
    is_proven,
    mismatched_signals,
)
from solution_intelligence.retrieval import IncidentContext


def make_hit(
    entry_id: str = "T",
    confidence: float = 0.9,
    similarity: float = 0.8,
) -> RetrievedSolution:
    entry = KnowledgeEntry(
        id=entry_id,
        source_type="ticket",
        title="vpn drops",
        description="",
        resolution="",
        worked_count=(5, 5),
    )
    return RetrievedSolution(entry=entry, score=similarity, confidence=confidence)


def test_thresholds_are_the_shared_constants():
    """Eval's ABSTAIN_THRESHOLD and chat's low band must stay in sync."""
    from solution_intelligence.evaluate import ABSTAIN_THRESHOLD as EVAL_ABSTAIN

    assert ABSTAIN_THRESHOLD == EVAL_ABSTAIN == 0.75
    assert CONFIDENT_THRESHOLD == 0.90
    assert ABSTAIN_THRESHOLD < CONFIDENT_THRESHOLD


def test_decide_proceeds_above_confident_band():
    verdict = decide(make_hit(confidence=0.95))
    assert verdict.action == "proceed"
    assert verdict.next_best_action is None


def test_decide_asks_for_context_in_middle_band():
    verdict = decide(
        make_hit(confidence=0.80), context=IncidentContext(error_code="E1")
    )
    assert verdict.action == "ask_context"
    nba = verdict.next_best_action
    assert nba is not None
    assert nba["action"] == "ask_context"
    # error_code was supplied; module and environment are missing.
    assert nba["missing_fields"] == ["module", "environment"]
    assert "module, environment" in nba["message"]


def test_ask_context_with_complete_context_does_not_re_ask():
    """Full context supplied but still mid-band: no re-asking for fields."""
    verdict = decide(
        make_hit(confidence=0.80),
        context=IncidentContext(error_code="E1", module="SAP MM", environment="PROD"),
    )
    assert verdict.action == "ask_context"
    nba = verdict.next_best_action
    assert nba is not None
    assert nba["missing_fields"] == []
    assert "specialist" in nba["message"]


def test_decide_escalates_below_abstain_threshold():
    """An unproven weak match still escalates (control case)."""
    hit = make_hit(confidence=0.50)
    hit.entry.worked_count = (0, 3)  # attempted 3, never worked
    assert is_proven(hit) is False
    verdict = decide(hit)
    assert verdict.action == "escalate_sme"
    nba = verdict.next_best_action
    assert nba is not None
    assert nba["action"] == "escalate_sme"
    assert nba["nearest_record"] == {"id": "T", "title": "vpn drops"}
    # No percentage: the composite score is a weighted blend, not a
    # probability, and a bare figure reads as "50% chance this is right".
    assert "50%" not in nba["message"]
    assert "closely enough to recommend" in nba["message"]


def test_decide_proven_record_bypasses_abstain():
    """A proven fix is a go once the confidence is above the floor and the
    query is topically about the record."""
    hit = make_hit(confidence=0.51)
    hit.entry.worked_count = (8, 8)  # proven fix
    assert is_proven(hit) is True
    assert hit.confidence >= PROVEN_FLOOR
    verdict = decide(hit, query="vpn keeps dropping every hour")
    assert verdict.action == "proceed"
    assert verdict.next_best_action is None


def test_decide_proven_record_off_topic_escalates():
    """A perfect track record is not enough when the query is about a
    different system: the success history is already inside the composite
    score, so it must not also veto the abstain decision."""
    hit = make_hit(confidence=0.51)
    hit.entry.worked_count = (8, 8)
    assert is_proven(hit) is True
    verdict = decide(hit, query="users cannot log in to outlook")
    assert verdict.action == "escalate_sme"


def test_decide_proven_record_below_floor_escalates():
    """Even a perfect track record is not enough at very low similarity —
    the banner still appears because the query likely isn't about this record."""
    hit = make_hit(confidence=0.29)
    hit.entry.worked_count = (45, 45)  # perfect track record
    assert is_proven(hit) is True
    assert hit.confidence < PROVEN_FLOOR
    verdict = decide(hit)
    assert verdict.action == "escalate_sme"


def test_decide_unproven_record_at_low_confidence_escalates():
    """Unproven weak match still escalates (explicit control)."""
    hit = make_hit(confidence=0.41)
    hit.entry.worked_count = (0, 3)  # attempted 3, never worked
    assert is_proven(hit) is False
    verdict = decide(hit)
    assert verdict.action == "escalate_sme"


def test_decide_under_min_attempts_is_not_proven():
    """A perfect record with too few attempts isn't trusted yet."""
    hit = make_hit(confidence=0.51)
    hit.entry.worked_count = (2, 2)  # perfect but only 2 attempts
    assert hit.entry.attempted < PROVEN_MIN_ATTEMPTS
    assert is_proven(hit) is False
    verdict = decide(hit)
    assert verdict.action == "escalate_sme"


def test_decide_with_no_hits_escalates_without_nearest():
    verdict = decide(None)
    assert verdict.action == "escalate_sme"
    nba = verdict.next_best_action
    assert nba is not None
    assert nba["nearest_record"] is None


def test_decide_is_deterministic():
    hit = make_hit(confidence=0.6)
    context = IncidentContext(environment="UAT")
    verdicts = [decide(hit, context=context) for _ in range(3)]
    assert all(v == verdicts[0] for v in verdicts)


def test_mismatched_signals_reports_conflicts_only():
    entry = make_hit().entry
    entry.error_code = "M8149"
    entry.module = "SAP MM"
    entry.environment = "PROD"
    context = IncidentContext(error_code="M8149", module="SAP MM", environment="UAT")
    # Only environment conflicts; code and module match.
    assert mismatched_signals(entry, context) == ["environment"]


def test_mismatched_signals_ignores_missing_fields():
    entry = make_hit().entry
    entry.error_code = "M8149"
    entry.environment = None
    context = IncidentContext(error_code="S_RFC", environment="PROD")
    # Entry has no environment recorded: absent vs PROD is not a conflict.
    assert mismatched_signals(entry, context) == ["error_code"]


def test_mismatched_signals_without_context_is_empty():
    assert mismatched_signals(make_hit().entry, None) == []


def test_context_trap_requires_match_and_conflict():
    entry = make_hit().entry
    entry.error_code = "M8149"
    entry.environment = "PROD"

    trap_context = IncidentContext(error_code="M8149", environment="UAT")
    hit = make_hit()
    hit.entry = entry
    hit.signals = ["error_code"]  # matched_signals computed by the ranker
    assert is_context_trap(hit, trap_context)

    # Same conflict but no matched signal: unrelated record, not a trap.
    hit_no_match = make_hit()
    hit_no_match.entry = entry
    hit_no_match.signals = []
    assert not is_context_trap(hit_no_match, trap_context)

    # Full match, no conflict: not a trap.
    ok_context = IncidentContext(error_code="M8149", environment="PROD")
    hit_ok = make_hit()
    hit_ok.entry = entry
    hit_ok.signals = ["error_code", "environment"]
    assert not is_context_trap(hit_ok, ok_context)


def test_verdict_is_frozen_dataclass():
    verdict = PolicyVerdict(action="proceed")
    with pytest.raises(Exception):
        verdict.action = "escalate_sme"  # type: ignore[misc]
