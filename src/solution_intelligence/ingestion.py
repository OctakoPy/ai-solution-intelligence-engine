"""Ingestion pipeline: Stage 1 filter -> AI judge -> duplicate check.

The pipeline is deliberately transparent and deterministic so a non-technical
audience can watch every entry be accepted, flagged, or rejected with a
clear reason. Where a live deployment would call a model, the demo uses
interpretable heuristics that mirror the same checklist.
"""

from __future__ import annotations

from collections.abc import Iterable

from solution_intelligence.models import (
    DuplicateResult,
    JudgeField,
    JudgeResult,
    KnowledgeEntry,
    PipelineRun,
    PipelineStep,
    Stage1Result,
    StageResult,
)

JUDGE_THRESHOLD = 0.6
EXACT_DUPLICATE_THRESHOLD = 0.95
NEAR_DUPLICATE_THRESHOLD = 0.85

# Words / phrases that strongly suggest a reusable, well-documented fix.
_GENERIC_RESOLUTION_WORDS = {
    "assigned",
    "checked",
    "confirmed",
    "configured",
    "created",
    "installed",
    "restarted",
    "replaced",
    "resolved",
    "restored",
    "set",
    "updated",
    "verified",
}

# Phrases typical of a one-off / non-reusable request.
_ONE_OFF_PHRASES = (
    "one-off",
    "one time",
    "one-time",
    "single request",
    "for audit",
    "test environment",
    "test only",
)


def _normalise(text: str) -> set[str]:
    """Return the set of lowercase words in a piece of text."""
    words = "".join(c if c.isalnum() else " " for c in text.lower()).split()
    return set(words)


class Stage1Filter:
    """Rule-based pre-filter that catches structural problems first."""

    def evaluate(self, entry: KnowledgeEntry) -> Stage1Result:
        """Return pass/fail plus the reasons behind it."""
        reasons: list[str] = []

        if entry.status.lower() not in {"resolved", "published", "active"}:
            reasons.append(f"status is '{entry.status}', not a resolved/usable state")

        if len(entry.resolution.strip()) < 20:
            reasons.append("no documented resolution (text too short)")

        if entry.quality_flag == "junk":
            reasons.append("marked as junk / low value")

        if entry.deprecated_reference:
            reasons.append("references a deprecated system")

        if entry.access_level == "restricted":
            reasons.append("restricted access content requires special handling")

        passed = len(reasons) == 0
        return Stage1Result(entry=entry, passed=passed, reasons=reasons)


class AIJudge:
    """Scores an entry against a five-point quality checklist.

    Each checklist field produces a 0..1 score. The overall score is the
    average and the entry passes if it clears ``JUDGE_THRESHOLD``.
    """

    def evaluate(self, entry: KnowledgeEntry) -> JudgeResult:
        """Run the checklist and produce an overall verdict."""
        fields: list[JudgeField] = []

        has_resolution = self._has_resolution(entry)
        fields.append(
            JudgeField(
                name="resolution",
                label="Has a documented resolution",
                score=has_resolution,
                explanation=(
                    "The entry includes a clear, actionable fix"
                    if has_resolution >= 1.0
                    else "No reusable resolution text found"
                ),
            )
        )

        reusable = self._is_reusable(entry)
        fields.append(
            JudgeField(
                name="reusable",
                label="Describes a reusable pattern",
                score=reusable,
                explanation=(
                    "Looks like a repeatable procedure rather than a one-off"
                    if reusable >= 0.5
                    else "Looks like a one-off / non-reusable incident"
                ),
            )
        )

        deprecated = 1.0 if not entry.deprecated_reference else 0.0
        fields.append(
            JudgeField(
                name="deprecated",
                label="Not tied to deprecated systems",
                score=deprecated,
                explanation=(
                    "Uses current, supported technology"
                    if deprecated == 1.0
                    else "References a retired / deprecated system"
                ),
            )
        )

        pii = self._free_of_pii(entry)
        fields.append(
            JudgeField(
                name="pii",
                label="Free of personal data",
                score=pii,
                explanation=(
                    "No obvious personal or confidential data"
                    if pii == 1.0
                    else "Contains personal / confidential data"
                ),
            )
        )

        detail = self._detail_score(entry)
        fields.append(
            JudgeField(
                name="detail",
                label="Sufficient detail to be useful",
                score=detail,
                explanation=(
                    "Rich title, description and resolution"
                    if detail >= 0.7
                    else "Thin on detail"
                ),
            )
        )

        overall = round(sum(f.score for f in fields) / len(fields), 3)
        # A clearly one-off incident can never be stored, regardless of score.
        if reusable == 0.0:
            overall = 0.0
        result = JudgeResult(
            entry=entry,
            fields=fields,
            overall=overall,
            passed=overall >= JUDGE_THRESHOLD,
            threshold=JUDGE_THRESHOLD,
        )
        return result

    @staticmethod
    def _has_resolution(entry: KnowledgeEntry) -> float:
        text = entry.resolution.strip()
        if len(text) < 20:
            return 0.0
        words = _normalise(text)
        if len(words) < 5:
            return 0.4
        if any(w in words for w in _GENERIC_RESOLUTION_WORDS):
            return 1.0
        return 0.7

    @staticmethod
    def _is_reusable(entry: KnowledgeEntry) -> float:
        combined = f"{entry.title} {entry.description} {entry.resolution}".lower()
        if any(phrase in combined for phrase in _ONE_OFF_PHRASES):
            return 0.0
        return 1.0

    @staticmethod
    def _free_of_pii(entry: KnowledgeEntry) -> float:
        combined = f"{entry.title} {entry.description} {entry.resolution}".lower()
        pii_markers = ("salary", "personal data", "confidential", "employee personal")
        if any(m in combined for m in pii_markers):
            return 0.2
        return 1.0

    @staticmethod
    def _detail_score(entry: KnowledgeEntry) -> float:
        combined = f"{entry.title} {entry.description} {entry.resolution}"
        words = len(combined.split())
        if words >= 40:
            return 1.0
        if words >= 25:
            return 0.8
        if words >= 12:
            return 0.5
        return 0.2


class DuplicateChecker:
    """Compares a new entry against the existing index using embeddings."""

    def __init__(self, embedder) -> None:
        self.embedder = embedder

    def evaluate(
        self,
        entry: KnowledgeEntry,
        indexed: list[KnowledgeEntry],
    ) -> DuplicateResult:
        """Return the duplicate tier and best matches for an entry."""
        if not indexed:
            return DuplicateResult(entry=entry, tier="unique")

        query_vec = self.embedder.embed(entry.full_text)
        scores: list[tuple[str, float]] = []
        for other in indexed:
            other_vec = self.embedder.embed(other.full_text)
            scores.append((other.id, self.embedder.similarity(query_vec, other_vec)))

        capped = [s for s in scores if s[1] >= NEAR_DUPLICATE_THRESHOLD]
        if not capped:
            return DuplicateResult(
                entry=entry,
                tier="unique",
                all_scores=_sorted(scores),
            )

        top_id, top_score = max(capped, key=lambda s: s[1])
        top = next(e for e in indexed if e.id == top_id)
        if top_score >= EXACT_DUPLICATE_THRESHOLD:
            tier = "exact_duplicate"
        else:
            tier = "near_duplicate"

        return DuplicateResult(
            entry=entry,
            tier=tier,
            best_match_id=top_id,
            best_match_title=top.title,
            best_score=top_score,
            all_scores=_sorted(scores),
        )


def _sorted(scores: list[tuple[str, float]]) -> list[tuple[str, float]]:
    return sorted(scores, key=lambda s: s[1], reverse=True)


class IngestionPipeline:
    """Runs every source entry through the full ingestion flow."""

    def __init__(
        self,
        stage1: Stage1Filter | None = None,
        judge: AIJudge | None = None,
        duplicate_checker: DuplicateChecker | None = None,
    ) -> None:
        self.stage1 = stage1 or Stage1Filter()
        self.judge = judge or AIJudge()
        self.duplicate_checker = duplicate_checker

    def run(
        self,
        entries: Iterable[KnowledgeEntry],
        *,
        collect_steps: bool = True,
    ) -> PipelineRun:
        """Ingest entries and return the pipeline record."""
        run = PipelineRun()
        indexed: list[KnowledgeEntry] = []

        for entry in entries:
            self._visualise(
                run, entry, "source", "Received from source", StageResult.PASS
            )

            stage1 = self.stage1.evaluate(entry)
            if not stage1.passed:
                detail = "; ".join(stage1.reasons) or "failed structural checks"
                self._visualise(run, entry, "stage1", detail, StageResult.REJECT)
                run.rejected.append(entry)
                continue
            self._visualise(
                run,
                entry,
                "stage1",
                "Passed structural checks",
                StageResult.PASS,
                score=1.0,
            )

            judge = self.judge.evaluate(entry)
            if not judge.passed:
                self._visualise(
                    run,
                    entry,
                    "judge",
                    f"AI quality score {judge.overall:.0%} below "
                    f"{judge.threshold:.0%} threshold",
                    StageResult.REJECT,
                    score=judge.overall,
                )
                run.rejected.append(entry)
                continue
            self._visualise(
                run,
                entry,
                "judge",
                f"AI quality score {judge.overall:.0%}",
                StageResult.PASS,
                score=judge.overall,
            )

            if self.duplicate_checker is not None:
                dup = self.duplicate_checker.evaluate(entry, indexed)
                if dup.tier == "exact_duplicate":
                    self._visualise(
                        run,
                        entry,
                        "duplicate",
                        f"Exact match with '{dup.best_match_title}' "
                        f"({dup.best_score:.0%}) - rejected as duplicate",
                        StageResult.REJECT,
                        score=dup.best_score,
                    )
                    run.rejected.append(entry)
                    continue
                if dup.tier == "near_duplicate":
                    self._visualise(
                        run,
                        entry,
                        "duplicate",
                        f"Near match ({dup.best_score:.0%}) - flagged for "
                        f"human merge review",
                        StageResult.FLAG,
                        score=dup.best_score,
                    )
                    # Kept visible for the demo but never indexed.
                    run.ingested.append(entry)
                    run.flagged.append(entry)
                    continue
                self._visualise(
                    run,
                    entry,
                    "duplicate",
                    "Unique - no close duplicate found",
                    StageResult.PASS,
                )
            else:
                self._visualise(
                    run,
                    entry,
                    "duplicate",
                    "Duplicate check skipped",
                    StageResult.PASS,
                )

            indexed.append(entry)
            run.ingested.append(entry)

        if not collect_steps:
            run.steps = []
        return run

    @staticmethod
    def _visualise(
        run: PipelineRun,
        entry: KnowledgeEntry,
        stage: str,
        label: str,
        result: StageResult,
        score: float | None = None,
    ) -> None:
        run.add(
            PipelineStep(
                entry=entry, stage=stage, label=label, result=result, score=score
            )
        )
