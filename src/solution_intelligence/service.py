"""High-level service tying sources, ingestion, and retrieval together.

This is the layer the demo UI talks to. It produces plain, display-ready
data so the front end can animate the four-source -> filter -> judge ->
index flow the demo audience expects.
"""

from __future__ import annotations

from solution_intelligence.agent import ConversationalAgent
from solution_intelligence.embeddings import LocalEmbedder
from solution_intelligence.ingestion import DuplicateChecker, IngestionPipeline
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
    ) -> None:
        self.embedder = embedder or LocalEmbedder()
        if duplicate_checker is None:
            duplicate_checker = DuplicateChecker(self.embedder)
        self.pipeline = IngestionPipeline(duplicate_checker=duplicate_checker)
        self.confidence = ConfidenceScorer()
        self.index = KnowledgeIndex(embedder=self.embedder)
        self.agent = ConversationalAgent(self.index)
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
        self.last_run = run
        return run

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
        weighted signal score - not by raw similarity alone.
        """
        return rank_results(
            index=self.index,
            query=query,
            top_k=top_k,
            context=context,
            adjust=None,
        )
