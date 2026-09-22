"""Tests for the pilot evaluation framework (issue #20)."""

import pytest

from solution_intelligence.evaluate import (
    ABSTAIN_THRESHOLD,
    EVAL_CASES,
    CaseResult,
    EvalCase,
    EvalReport,
    comparison,
    evaluate,
    format_report,
)
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
    date: str = "2025-01-01",
) -> KnowledgeEntry:
    """Build a minimal indexed entry for synthetic eval tests."""
    return KnowledgeEntry(
        id=entry_id,
        source_type="ticket",
        title=title,
        description=f"Description for {title}",
        resolution="Applied the standard fix and confirmed it works.",
        category="sap_authorization",
        date=date,
        worked_count=worked,
        error_code=error_code,
        module=module,
        environment=environment,
    )


@pytest.fixture(scope="module")
def engine():
    """A small synthetic engine so metric tests are deterministic and fast."""
    eng = SolutionEngine()
    eng.ingest(
        [
            make_entry("VPN", "VPN keeps dropping after five minutes"),
            make_entry(
                "PRINTER",
                "Printer is jammed and needs new toner",
                worked=(1, 5),
            ),
            make_entry(
                "PROD-FIX",
                "Goods receipt posting error account determination not found",
                worked=(8, 8),
                error_code="M8149",
                module="SAP MM",
                environment="PROD",
            ),
            make_entry(
                "UAT-FIX",
                "Goods receipt posting error in UAT sandbox",
                worked=(4, 4),
                error_code="M8149",
                module="SAP MM",
                environment="UAT",
            ),
        ],
        collect_steps=False,
    )
    return eng


# --- Case construction and validation --------------------------------------


def test_eval_case_requires_exactly_one_outcome():
    with pytest.raises(ValueError):
        EvalCase(case_id="bad", query="q")  # neither expected_id nor abstain
    with pytest.raises(ValueError):
        EvalCase(case_id="bad", query="q", expected_id="X", abstain=True)
    assert EvalCase(case_id="ok", query="q", expected_id="X")
    assert EvalCase(case_id="ok", query="q", abstain=True)


def test_eval_case_without_context_strips_context():
    case = EvalCase(
        case_id="c",
        query="q",
        context=IncidentContext(error_code="M8149"),
        expected_id="X",
    )
    assert case.without_context().context is None
    assert case.context is not None  # original untouched


def test_eval_cases_are_well_formed():
    assert EVAL_CASES
    for case in EVAL_CASES:
        assert case.case_id and case.query
    abstain_cases = [c for c in EVAL_CASES if c.abstain]
    assert abstain_cases, "eval must include honest-gap cases"
    assert any(c.context for c in EVAL_CASES), "eval must include context cases"


# --- Metric math on hand-built results (no engine needed) -------------------


def hand_report() -> EvalReport:
    """Build a report with known outcomes for metric math tests."""

    def result(case: EvalCase, rank: int | None, top_score: float) -> CaseResult:
        top_ids = tuple(f"X{i}" for i in range(1, 6))
        if rank is not None:
            top_ids = tuple("EXPECTED" if i == rank else f"X{i}" for i in range(1, 6))
        return CaseResult(
            case=case,
            rank=rank,
            top_ids=top_ids[:5],
            top_score=top_score,
            abstained=top_score < ABSTAIN_THRESHOLD,
            hit=rank is not None and rank <= case.expected_top_k,
            top1=rank == 1,
        )

    report = EvalReport(label="test")
    report.add(result(EvalCase(case_id="a", query="q", expected_id="E"), 1, 0.9))
    report.add(result(EvalCase(case_id="b", query="q", expected_id="E"), 3, 0.5))
    report.add(result(EvalCase(case_id="c", query="q", expected_id="E"), None, 0.4))
    report.add(result(EvalCase(case_id="gap", query="q", abstain=True), None, 0.3))
    return report


def test_report_metric_math():
    report = hand_report()
    assert report.top1_rate == pytest.approx(1 / 3)
    assert report.topk_rate == pytest.approx(2 / 3)
    assert report.mrr == pytest.approx((1.0 + 1 / 3 + 0.0) / 3)
    assert report.mean_score_on_hits == pytest.approx((0.9 + 0.5) / 2)
    assert report.mean_score_on_misses == pytest.approx(0.4)
    assert report.abstain_precision == pytest.approx(1.0)


def test_report_empty_is_zeroed():
    report = EvalReport(label="empty")
    assert report.top1_rate == 0.0
    assert report.topk_rate == 0.0
    assert report.mrr == 0.0
    assert report.mean_score_on_hits == 0.0
    assert report.mean_score_on_misses == 0.0
    assert report.abstain_precision == 0.0
    assert report.trap_resisted is None


def test_report_as_dict_keys_are_stable():
    summary = hand_report().as_dict()
    assert summary["label"] == "test"
    assert summary["cases"] == 4
    assert set(summary) == {
        "label",
        "cases",
        "top1_rate",
        "topk_rate",
        "mrr",
        "mean_confidence_on_hits",
        "mean_confidence_on_misses",
        "abstain_precision",
        "trap_resisted",
    }


def test_format_report_is_deterministic():
    first = format_report(hand_report())
    second = format_report(hand_report())
    assert first == second
    assert "top-1 rate" in first
    assert "abstain precision" in first
    assert "Per-case outcomes" in first


# --- End-to-end over a synthetic engine -------------------------------------


def test_evaluate_context_mode_ranks_exact_context_match_first(engine):
    """With PROD context the PROD record outranks the UAT look-alike."""
    # Replicate the canonical PROD case's ranking through the engine and
    # grade it with the harness's own expectations.
    results = engine.search(
        "goods receipt posting error account determination not found",
        top_k=3,
        context=IncidentContext(
            error_code="M8149", module="SAP MM", environment="PROD"
        ),
    )
    assert results[0].entry.id == "PROD-FIX"
    assert results[0].confidence >= results[1].confidence


def test_evaluate_similarity_mode_judges_on_similarity(engine):
    report = evaluate(engine, mode="similarity", top_k=5)
    assert len(report.cases) == len(EVAL_CASES)
    assert all(0.0 <= c.top_score <= 1.0 for c in report.cases)
    # Similarity mode reuses index.query, so its ordering must match the
    # index's own similarity ordering for the same query.
    direct = engine.index.query("vpn keeps dropping", top_k=5)
    case_result = next(
        c
        for c in report.cases
        if c.case.query
        == "vpn keeps dropping after a few mins on windows 11 and wont reconnect"
    )
    assert case_result.top_ids[:1] == (direct[0].entry.id,)


def test_evaluate_rejects_unknown_mode(engine):
    with pytest.raises(ValueError):
        evaluate(engine, mode="bogus")  # type: ignore[arg-type]


def test_comparison_returns_all_modes(engine):
    reports = comparison(engine)
    assert set(reports) == {"similarity", "no_context", "context"}
    for report in reports.values():
        assert len(report.cases) == len(EVAL_CASES)
    # Same cases in every mode, so metrics are like-for-like.
    ids = {c.case.case_id for c in reports["context"].cases}
    for report in reports.values():
        assert {c.case.case_id for c in report.cases} == ids


def test_comparison_reports_are_deterministic(engine):
    first = comparison(engine)
    second = comparison(engine)
    for mode in first:
        assert format_report(first[mode]) == format_report(second[mode])


# --- Slow integration over the full real dataset ----------------------------


@pytest.mark.slow
def test_full_dataset_context_mode_beats_or_matches_no_context():
    """On the labeled set, adding context must not degrade top-1 retrieval."""
    reports = comparison(max_entries=78)
    context = reports["context"]
    no_context = reports["no_context"]
    assert context.top1_rate >= no_context.top1_rate
    # The UAT context trap must rank the UAT record first, not the PROD one.
    assert context.trap_resisted is True


@pytest.mark.slow
def test_full_dataset_honest_gaps_score_below_threshold():
    """Gap cases must not score confidently in the shipped mode."""
    report = evaluate(mode="context", max_entries=78)
    for case in report.abstain_cases:
        assert case.top_score < ABSTAIN_THRESHOLD, (
            f"{case.case.case_id} scored confidently on a known gap"
        )
