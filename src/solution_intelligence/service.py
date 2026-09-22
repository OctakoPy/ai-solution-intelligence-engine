"""High-level service tying sources, ingestion, and retrieval together.

This is the layer the demo UI talks to. It produces plain, display-ready
data so the front end can animate the four-source -> filter -> judge ->
index flow the demo audience expects.
"""

from __future__ import annotations

from solution_intelligence.agent import ConversationalAgent
from solution_intelligence.embeddings import LocalEmbedder
from solution_intelligence.ingestion import DuplicateChecker, IngestionPipeline
from solution_intelligence.memory import OutcomeRecord, ResolutionMemory
from solution_intelligence.models import (
    KnowledgeEntry,
    PipelineRun,
    RetrievedSolution,
)
from solution_intelligence.retrieval import (
    ConfidenceScorer,
    IncidentContext,
    KnowledgeIndex,
    rank_results,
)


class SolutionEngine:
    """Orchestrates the full demo ingestion -> retrieval flow."""

    def __init__(
        self,
        embedder: LocalEmbedder | None = None,
        duplicate_checker=None,
        memory: ResolutionMemory | None = None,
    ) -> None:
        self.embedder = embedder or LocalEmbedder()
        if duplicate_checker is None:
            duplicate_checker = DuplicateChecker(self.embedder)
        self.pipeline = IngestionPipeline(duplicate_checker=duplicate_checker)
        self.confidence = ConfidenceScorer()
        self.index = KnowledgeIndex(embedder=self.embedder)
        self.agent = ConversationalAgent(self.index)
        # Default to an in-memory store so the library stays deterministic
        # and side-effect free; persistent apps pass their own
        # ``ResolutionMemory`` (see apps/api/engine_cache.py).
        self.memory = memory if memory is not None else ResolutionMemory(path=None)
        self.last_run: PipelineRun | None = None

    def ingest(
        self,
        entries: list[KnowledgeEntry],
        *,
        collect_steps: bool = True,
    ) -> PipelineRun:
        """Run the pipeline and index everything that passes."""
        run = self.pipeline.run(entries, collect_steps=collect_steps)
        for entry in run.indexed:
            self.index.add(entry)
        # Fold any previously confirmed outcomes into the freshly indexed
        # records so learning survives re-ingestion (idempotent by design).
        self.memory.apply(self.index.entries)
        self.last_run = run
        return run

    def record_outcome(
        self,
        entry_id: str,
        success: bool,
        *,
        note: str = "",
        context: IncidentContext | None = None,
        source: str = "api",
    ) -> OutcomeRecord:
        """Record a confirmed outcome and fold it back into ranking.

        This is the write-back half of the Resolution Memory loop: a
        consultant confirms whether the recommended resolution worked, the
        outcome is appended to the memory log, and the affected record's
        ``worked_count`` is adjusted so the next search ranks it
        accordingly. A confirmed failure demotes the candidate (negative
        learning) exactly as a confirmed success boosts it.

        Args:
            entry_id: Id of the knowledge record the outcome is about.
            success: Whether the resolution actually worked.
            note: Optional free-text context from the consultant.
            context: Optional incident context captured with the outcome.
            source: Where the outcome came from (``"api"``, ``"ui"``).

        Returns:
            The stored :class:`OutcomeRecord`.

        Raises:
            KeyError: When ``entry_id`` is not in the index.
        """
        if self.index.get(entry_id) is None:
            raise KeyError(f"unknown entry id: {entry_id!r}")
        record = self.memory.record(
            entry_id,
            success,
            note=note,
            context=context,
            source=source,
        )
        self.memory.apply(self.index.entries)
        return record

    def search(
        self,
        query: str,
        top_k: int = 5,
        context: IncidentContext | None = None,
    ) -> list[RetrievedSolution]:
        """Retrieve solutions for a new issue with confidence scores.

        Args:
            query: Free-text description of the issue.
            top_k: Maximum number of candidates to return.
            context: Optional structured incident context (error code,
                module, environment) used by the confidence scorer's match
                signals.

        Results are ranked by outcome-aware confidence - the deterministic
        weighted signal score - not by raw similarity alone. Confirmed
        outcomes recorded via :meth:`record_outcome` feed the success-rate
        signal, so the ranking reflects what has actually worked.
        """
        return rank_results(
            index=self.index,
            query=query,
            top_k=top_k,
            context=context,
            adjust=None,
        )
