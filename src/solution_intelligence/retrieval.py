"""Retrieval: match new issues to curated solutions with trust metadata."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Callable

from solution_intelligence.embeddings import LocalEmbedder
from solution_intelligence.models import (
    KnowledgeEntry,
    RetrievedSolution,
)

# Deterministic, auditable weights for the outcome-aware confidence score.
# They sum to 1.0 and mirror the ranking signals proposed for the engine:
# semantic similarity, exact error-code match, module match, environment
# match, historical success rate, recency decay, and consultant feedback.
SIGNAL_WEIGHTS = {
    "semantic": 0.25,
    "error_code": 0.15,
    "module": 0.15,
    "environment": 0.10,
    "success": 0.20,
    "recency": 0.10,
    "feedback": 0.05,
}

# Older solutions decay at half-life cadence: a record this many days old
# contributes 50% of its recency signal.
RECENCY_HALF_LIFE_DAYS = 365


@dataclass(frozen=True)
class IncidentContext:
    """Structured context extracted from a new incident.

    Populated from the incident record (error code, affected system/module,
    and environment) so ranking can reward exact matches and penalize
    context mismatches - the "same error code, different root cause" trap.
    """

    error_code: str | None = None
    module: str | None = None
    environment: str | None = None

    def __bool__(self) -> bool:
        """True when the incident carries at least one structured signal."""
        return any((self.error_code, self.module, self.environment))


class KnowledgeIndex:
    """Searchable index built from ingested entries."""

    def __init__(self, embedder: LocalEmbedder | None = None) -> None:
        self.embedder = embedder or LocalEmbedder()
        self._vectors: dict[str, list[float]] = {}
        self._entries: dict[str, KnowledgeEntry] = {}

    def add(self, entry: KnowledgeEntry) -> None:
        """Index a single entry."""
        self._vectors[entry.id] = self.embedder.embed(entry.full_text)
        self._entries[entry.id] = entry

    def get(self, entry_id: str) -> KnowledgeEntry | None:
        """Look up an entry by id."""
        return self._entries.get(entry_id)

    @property
    def size(self) -> int:
        """Number of entries in the index."""
        return len(self._entries)

    @property
    def entries(self) -> list[KnowledgeEntry]:
        """All indexed entries."""
        return list(self._entries.values())

    def query(self, text: str, top_k: int = 5) -> list[RetrievedSolution]:
        """Return the top-k matches for a free-text issue description."""
        query_vec = self.embedder.embed(text, for_query=True)
        scored: list[tuple[str, float]] = []
        for entry_id, vec in self._vectors.items():
            scored.append((entry_id, self.embedder.similarity(query_vec, vec)))
        scored.sort(key=lambda s: s[1], reverse=True)

        results: list[RetrievedSolution] = []
        for entry_id, score in scored[:top_k]:
            entry = self._entries[entry_id]
            results.append(
                RetrievedSolution(
                    entry=entry,
                    score=round(score, 3),
                    confidence=0.5,  # replaced by judge confidence if available
                )
            )
        return results


class ConfidenceScorer:
    """Attaches an outcome-aware confidence score to retrieved solutions.

    Confidence is a deterministic weighted sum of seven signals: semantic
    similarity, exact error-code match, module match, environment match,
    historical success rate, recency decay, and consultant feedback. The
    match signals are only rewarded when the incident carries structured
    context; without context they contribute nothing rather than guessing.

        >>> scorer = ConfidenceScorer()
        >>> entry = KnowledgeEntry(
        ...     id="X", source_type="ticket", title="t", description="d",
        ...     resolution="r", worked_count=(9, 9),
        ... )
        >>> scorer.score(entry, 0.9)
        0.425
    """

    def score(
        self,
        entry: KnowledgeEntry,
        similarity: float,
        context: IncidentContext | None = None,
    ) -> float:
        """Return a composite 0..1 confidence score for a candidate.

        Args:
            entry: The candidate solution record.
            similarity: Semantic similarity of the incident to the entry (0..1).
            context: Optional structured incident context used by the
                error-code, module, and environment match signals.
        """
        success = entry.success_rate
        base = (
            SIGNAL_WEIGHTS["semantic"] * similarity
            + SIGNAL_WEIGHTS["error_code"] * _error_code_match(entry, context)
            + SIGNAL_WEIGHTS["module"] * _module_match(entry, context)
            + SIGNAL_WEIGHTS["environment"] * _environment_match(entry, context)
            + SIGNAL_WEIGHTS["success"] * success
            + SIGNAL_WEIGHTS["recency"] * _recency_score(entry)
            + SIGNAL_WEIGHTS["feedback"] * _feedback_score(entry)
        )
        return round(min(1.0, max(0.0, base)), 3)


def matched_signals(
    entry: KnowledgeEntry,
    context: IncidentContext | None,
) -> list[str]:
    """Names of the structured context signals that matched this entry.

    Deterministic and cheap, so the API can attach a transparent "what
    matched" readout to every retrieved solution. Returns an empty list
    when no context (or no matching signal) is present.
    """
    signals = []
    if _error_code_match(entry, context) > 0:
        signals.append("error_code")
    if _module_match(entry, context) > 0:
        signals.append("module")
    if _environment_match(entry, context) > 0:
        signals.append("environment")
    return signals


def rank_results(
    index: KnowledgeIndex,
    query: str,
    top_k: int = 5,
    context: IncidentContext | None = None,
    adjust: Callable[[RetrievedSolution], None] | None = None,
) -> list[RetrievedSolution]:
    """Rank retrieval candidates by outcome-aware confidence.

    This is the single ranking path shared by Find a Solution and the chat
    agent, so both surfaces rank identically for the same query and context,
    and what the UI shows for a candidate is the number it was ranked by:

    * a wider similarity pool is fetched first (3x) so a confident candidate
      is not cut off by a similarity-only top-k;
    * each candidate gets its deterministic confidence and matched signals;
    * results are then ranked by that confidence and trimmed to ``top_k``.

    ``adjust`` optionally mutates raw similarity before scoring; the chat
    agent uses it to nudge wordier conversational queries without introducing
    a second ranking scale.

    Returns:
        The ``top_k`` highest-confidence candidates, best first.
    """
    pool = index.query(query, top_k=max(top_k * 3, 3))
    for candidate in pool:
        if adjust is not None:
            adjust(candidate)
        candidate.confidence = ConfidenceScorer().score(
            candidate.entry, candidate.score, context
        )
        candidate.signals = matched_signals(candidate.entry, context)
    # Deterministic ordering: confidence (the ranked-by value) desc, then
    # success rate and similarity as tie-breakers, and finally entry id
    # ascending so equal-scoring candidates always surface in the same
    # order. Two stable passes keep the intent readable.
    pool.sort(key=lambda c: c.entry.id)
    pool.sort(
        key=lambda c: (c.confidence, c.entry.success_rate, c.score),
        reverse=True,
    )
    return pool[:top_k]


def _normalize(value: str | None) -> str:
    """Lower-case, trimmed form used for match comparisons."""
    return (value or "").strip().lower()


def _error_code_match(
    entry: KnowledgeEntry,
    context: IncidentContext | None,
) -> float:
    """1.0 when the incident error code exactly matches the record's."""
    if context is None or not context.error_code or not entry.error_code:
        return 0.0
    return float(_normalize(entry.error_code) == _normalize(context.error_code))


def _module_match(
    entry: KnowledgeEntry,
    context: IncidentContext | None,
) -> float:
    """Fraction of incident module terms matched by the record's module.

    Token overlap gives partial credit for a shared system token (e.g.
    "SAP CO" vs "SAP FICO" both share "SAP") while an exact module still
    scores 1.0.
    """
    if context is None or not context.module or not entry.module:
        return 0.0
    incident_terms = set(context.module.lower().split())
    entry_terms = set(entry.module.lower().split())
    if not incident_terms:
        return 0.0
    return len(incident_terms & entry_terms) / len(incident_terms)


def _environment_match(
    entry: KnowledgeEntry,
    context: IncidentContext | None,
) -> float:
    """1.0 when incident and record environments match exactly."""
    if context is None or not context.environment or not entry.environment:
        return 0.0
    return float(_normalize(entry.environment) == _normalize(context.environment))


def _recency_score(entry: KnowledgeEntry) -> float:
    """Decay a record's freshness with age, using a half-life model.

    Records with no parseable date contribute no recency signal.
    """
    if not entry.date.strip():
        return 0.0
    try:
        recorded = datetime.strptime(entry.date.strip(), "%Y-%m-%d").date()
    except ValueError:
        return 0.0
    age_days = max(0, (date.today() - recorded).days)
    return 0.5 ** (age_days / RECENCY_HALF_LIFE_DAYS)


def _feedback_score(entry: KnowledgeEntry) -> float:
    """Clamped consultant feedback fraction (0..1)."""
    return max(0.0, min(1.0, float(entry.feedback_score)))
