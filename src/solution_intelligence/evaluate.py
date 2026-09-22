"""Pilot evaluation framework for outcome-aware retrieval.

Runs a labeled set of query -> expected-solution cases through the live
retrieval path and measures whether outcome-aware ranking actually helps:
top-1 success rate, top-3 success rate, mean reciprocal rank, and a
confidence calibration readout (do high-confidence picks match, and do the
cases with no good answer score low enough to abstain?).

Three ranking modes can be compared on the same cases:

* ``"similarity"`` — raw similarity ranking via ``KnowledgeIndex.query``
  (the pre-outcome-aware baseline);
* ``"no_context"`` — outcome-aware confidence ranking, but structured
  incident context is dropped (isolates the value of the match signals);
* ``"context"`` — the shipped behavior: outcome-aware confidence ranking
  with the case's incident context when it defines one.

The eval is deterministic for a fixed dataset and embedder: the same inputs
always produce the same report.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from solution_intelligence.models import RetrievedSolution
from solution_intelligence.retrieval import IncidentContext
from solution_intelligence.service import SolutionEngine
from solution_intelligence.sources import load_filtered

# Chat abstain policy mirror: below this the engine will not offer a fix.
# Confidence modes apply it on the confidence scale (the chat policy's
# scale); similarity mode applies the same numeric bar to raw similarity
# as a rough like-for-like baseline.
ABSTAIN_THRESHOLD = 0.75

# Context-trap case: the UAT incident must not resolve to the PROD record.
TRAP_PROD_ID = "TIC-3011"
TRAP_UAT_ID = "TIC-3012"

Mode = str  # "similarity" | "no_context" | "context"


@dataclass(frozen=True)
class EvalCase:
    """One labeled query with its expected outcome.

    Exactly one of ``expected_id`` (this solution must be retrieved) or
    ``abstain=True`` (no good answer exists; the engine must not pretend)
    must be set.
    """

    case_id: str
    query: str
    context: IncidentContext | None = None
    expected_id: str | None = None
    expected_top_k: int = 3
    abstain: bool = False

    def __post_init__(self) -> None:
        if (self.expected_id is not None) == self.abstain:
            raise ValueError(
                f"case {self.case_id!r}: exactly one of expected_id / abstain "
                "must be set"
            )

    def without_context(self) -> "EvalCase":
        """Copy of this case with its structured context stripped."""
        return EvalCase(
            case_id=self.case_id,
            query=self.query,
            context=None,
            expected_id=self.expected_id,
            expected_top_k=self.expected_top_k,
            abstain=self.abstain,
        )


def _context(
    error_code: str | None = None,
    module: str | None = None,
    environment: str | None = None,
) -> IncidentContext:
    return IncidentContext(
        error_code=error_code, module=module, environment=environment
    )


# Labeled cases derived from the demo dataset's ``demo_tag`` values. Queries
# are phrased as a real support agent would type them (see
# docs/tutorials/demo-script.md); expected ids are the records the demo
# script promises.
EVAL_CASES: tuple[EvalCase, ...] = (
    # --- Top-1 retrievals (canonical demo scenarios) ------------------------
    EvalCase(
        case_id="canonical_fi_auth",
        query=(
            "user can't get into FI reports in sap fico, "
            "getting not authorized this morning"
        ),
        expected_id="TIC-1001",
    ),
    EvalCase(
        case_id="near_duplicate_co_variant",
        query=(
            "employee blocked from CO cost center controlling reports, "
            "auth error on the transaction"
        ),
        expected_id="TIC-1004",
    ),
    EvalCase(
        case_id="vpn_auto_resolve",
        query="vpn keeps dropping after a few mins on windows 11 and wont reconnect",
        expected_id="TIC-1008",
    ),
    EvalCase(
        case_id="kb_onboarding_policy",
        query="how do i set up a laptop for a new employee, whats the standard?",
        expected_id="KB_-1037",
    ),
    EvalCase(
        case_id="chat_batch_job",
        query=(
            "the nightly sap batch job for inventory reconciliation "
            "keeps short dumping. how do i fix it?"
        ),
        expected_id="TIC-1031",
    ),
    # --- Context-aware cases (need IncidentContext to rank correctly) ------
    EvalCase(
        case_id="context_prod_canonical",
        query="goods receipt posting error account determination not found",
        context=_context("M8149", "SAP MM", "PROD"),
        expected_id="TIC-3011",
    ),
    EvalCase(
        case_id="context_uat_trap",
        query="goods receipt posting error account determination not found",
        context=_context("M8149", "SAP MM", "UAT"),
        expected_id="TIC-3012",
    ),
    EvalCase(
        case_id="context_co_vs_fico",
        query="authorization error on financial reports",
        context=_context("S_RS_COMP", "SAP CO"),
        expected_id="TIC-1004",
    ),
    # --- Honest-gap cases: no good answer exists in the index ---------------
    EvalCase(
        case_id="gap_fiori_tile",
        query=(
            "the po approval tile is missing from fiori launchpad "
            "for a few users after this weeks update"
        ),
        abstain=True,
    ),
    EvalCase(
        case_id="gap_zreport99",
        query=(
            "the new quarterly compliance export is coming up and the custom "
            "abap program zreport99 keeps erroring. any known fix?"
        ),
        abstain=True,
    ),
    EvalCase(
        case_id="gap_addon_timeouts",
        query="third party sap add on makes sessions time out much faster than usual",
        abstain=True,
    ),
)


@dataclass(frozen=True)
class CaseResult:
    """Outcome of one eval case against the live engine."""

    case: EvalCase
    rank: int | None  # 1-based rank of expected_id; None when not retrieved
    top_ids: tuple[str, ...]
    top_score: float  # score the ranking was judged on (confidence, or similarity)
    abstained: bool  # top score below the abstain threshold
    hit: bool  # expected found within expected_top_k
    top1: bool  # expected is the rank-1 candidate

    @property
    def reciprocal_rank(self) -> float:
        """1 / rank, or 0.0 when the expected solution was not retrieved."""
        return 0.0 if self.rank is None else 1.0 / self.rank


@dataclass
class EvalReport:
    """Aggregated metrics over all cases for one ranking mode."""

    label: str
    score_kind: str = "confidence"  # what ``top_score`` measures
    cases: list[CaseResult] = field(default_factory=list)

    def add(self, result: CaseResult) -> None:
        self.cases.append(result)

    @property
    def retrieval_cases(self) -> list[CaseResult]:
        """Cases where a specific solution was expected."""
        return [c for c in self.cases if not c.case.abstain]

    @property
    def abstain_cases(self) -> list[CaseResult]:
        """Cases where the engine was expected to abstain."""
        return [c for c in self.cases if c.case.abstain]

    @property
    def top1_rate(self) -> float:
        """Share of retrieval cases where the expected solution ranked #1."""
        cases = self.retrieval_cases
        if not cases:
            return 0.0
        return sum(c.top1 for c in cases) / len(cases)

    @property
    def topk_rate(self) -> float:
        """Share of retrieval cases where the expected solution made top-k."""
        cases = self.retrieval_cases
        if not cases:
            return 0.0
        return sum(c.hit for c in cases) / len(cases)

    @property
    def mrr(self) -> float:
        """Mean reciprocal rank over retrieval cases (0 when never found)."""
        cases = self.retrieval_cases
        if not cases:
            return 0.0
        return sum(c.reciprocal_rank for c in cases) / len(cases)

    @property
    def mean_score_on_hits(self) -> float:
        """Mean top score across retrieval cases that were hits."""
        hits = [c for c in self.retrieval_cases if c.hit]
        if not hits:
            return 0.0
        return sum(c.top_score for c in hits) / len(hits)

    @property
    def mean_score_on_misses(self) -> float:
        """Mean top score across retrieval cases that missed."""
        misses = [c for c in self.retrieval_cases if not c.hit]
        if not misses:
            return 0.0
        return sum(c.top_score for c in misses) / len(misses)

    @property
    def abstain_precision(self) -> float:
        """Share of honest-gap cases where the engine actually abstained."""
        cases = self.abstain_cases
        if not cases:
            return 0.0
        return sum(c.abstained for c in cases) / len(cases)

    @property
    def trap_resisted(self) -> bool | None:
        """UAT context trap: the expected UAT record ranked #1, not PROD.

        ``None`` when the trap case is not part of this report.
        """
        trap = next(
            (c for c in self.cases if c.case.case_id == "context_uat_trap"), None
        )
        if trap is None:
            return None
        return trap.top_ids[:1] == (TRAP_UAT_ID,)

    def as_dict(self) -> dict[str, float | int | str | bool | None]:
        """Machine-readable summary for notebooks and dashboards."""
        return {
            "label": self.label,
            "cases": len(self.cases),
            "top1_rate": round(self.top1_rate, 3),
            "topk_rate": round(self.topk_rate, 3),
            "mrr": round(self.mrr, 3),
            f"mean_{self.score_kind}_on_hits": round(self.mean_score_on_hits, 3),
            f"mean_{self.score_kind}_on_misses": round(self.mean_score_on_misses, 3),
            "abstain_precision": round(self.abstain_precision, 3),
            "trap_resisted": self.trap_resisted,
        }


def _make_engine(max_entries: int | None) -> SolutionEngine:
    """Build and ingest an engine over the demo dataset."""
    engine = SolutionEngine()
    engine.ingest(load_filtered(max_total=max_entries), collect_steps=False)
    return engine


def _run_confidence_case(
    engine: SolutionEngine,
    case: EvalCase,
    top_k: int,
    with_context: bool,
) -> CaseResult:
    """Run a case through the outcome-aware ranking path."""
    effective = case if with_context else case.without_context()
    results: list[RetrievedSolution] = engine.search(
        effective.query, top_k=top_k, context=effective.context
    )
    top_ids = tuple(r.entry.id for r in results)
    top_score = results[0].confidence if results else 0.0
    rank: int | None = None
    if case.expected_id in top_ids:
        rank = top_ids.index(case.expected_id) + 1
    hit = rank is not None and rank <= case.expected_top_k
    return CaseResult(
        case=case,
        rank=rank,
        top_ids=top_ids,
        top_score=round(top_score, 3),
        abstained=top_score < ABSTAIN_THRESHOLD,
        hit=hit,
        top1=rank == 1,
    )


def _run_similarity_case(
    engine: SolutionEngine, case: EvalCase, top_k: int
) -> CaseResult:
    """Run a case through raw similarity ranking (pre-outcome-aware baseline)."""
    results = engine.index.query(case.query, top_k=top_k)
    top_ids = tuple(r.entry.id for r in results)
    top_score = results[0].score if results else 0.0
    rank: int | None = None
    if case.expected_id in top_ids:
        rank = top_ids.index(case.expected_id) + 1
    hit = rank is not None and rank <= case.expected_top_k
    return CaseResult(
        case=case,
        rank=rank,
        top_ids=top_ids,
        top_score=round(top_score, 3),
        abstained=top_score < ABSTAIN_THRESHOLD,
        hit=hit,
        top1=rank == 1,
    )


def evaluate(
    engine: SolutionEngine | None = None,
    *,
    mode: Mode = "context",
    max_entries: int | None = 78,
    top_k: int = 5,
) -> EvalReport:
    """Run all eval cases against the live retrieval path.

    Args:
        engine: A prepared engine. When omitted, a fresh engine ingests the
            demo dataset (capped at ``max_entries``).
        mode: ``"context"`` (outcome-aware ranking with incident context),
            ``"no_context"`` (outcome-aware ranking, context dropped), or
            ``"similarity"`` (raw similarity ranking baseline).
        max_entries: Dataset cap used when building the default engine.
        top_k: Candidate pool size per case.

    Returns:
        An :class:`EvalReport` with per-case outcomes and aggregate metrics.
    """
    if mode not in ("similarity", "no_context", "context"):
        raise ValueError(f"unknown mode: {mode!r}")
    if engine is None:
        engine = _make_engine(max_entries)
    report = EvalReport(label=mode)
    for case in EVAL_CASES:
        if mode == "similarity":
            result = _run_similarity_case(engine, case, top_k)
        else:
            result = _run_confidence_case(
                engine, case, top_k, with_context=mode == "context"
            )
        report.add(result)
    return report


def comparison(
    engine: SolutionEngine | None = None,
    *,
    max_entries: int | None = 78,
    top_k: int = 5,
) -> dict[str, EvalReport]:
    """Run the eval in all modes on one engine for a like-for-like comparison.

    Returns:
        Reports keyed by mode: ``"similarity"``, ``"no_context"``,
        ``"context"``.
    """
    if engine is None:
        engine = _make_engine(max_entries)
    return {
        mode: evaluate(engine, mode=mode, top_k=top_k)
        for mode in ("similarity", "no_context", "context")
    }


def format_report(report: EvalReport) -> str:
    """Render a deterministic, human-readable eval report.

    Plain ASCII so the output is stable on every console and platform.
    """
    lines: list[str] = [f"Eval report - {report.label}", "=" * (13 + len(report.label))]
    n_ret = len(report.retrieval_cases)
    n_abs = len(report.abstain_cases)
    lines.append(
        f"top-1 rate:          {report.top1_rate:6.1%}  ({sum(c.top1 for c in report.retrieval_cases)}/{n_ret})"
    )
    lines.append(
        f"top-3 rate:          {report.topk_rate:6.1%}  ({sum(c.hit for c in report.retrieval_cases)}/{n_ret})"
    )
    lines.append(f"mean reciprocal rank:{report.mrr:8.3f}")
    lines.append(
        f"mean {report.score_kind} on hits: {report.mean_score_on_hits:5.3f}"
        f"   on misses: {report.mean_score_on_misses:.3f}"
    )
    lines.append(
        f"abstain precision:   {report.abstain_precision:6.1%}  ({sum(c.abstained for c in report.abstain_cases)}/{n_abs})"
    )
    trap = report.trap_resisted
    if trap is not None:
        lines.append(f"UAT trap resisted:   {trap!s:>6}")
    lines.append("")
    lines.append("Per-case outcomes:")
    for c in report.cases:
        outcome = "abstain-ok" if c.case.abstain else ("HIT" if c.hit else "MISS")
        rank = "-" if c.rank is None else str(c.rank)
        lines.append(
            f"  {c.case.case_id:28} {outcome:10} rank={rank:>2}  "
            f"top_{report.score_kind}={c.top_score:.3f}"
        )
    return "\n".join(lines)
