"""Retrieval: match new issues to curated solutions with trust metadata."""

from __future__ import annotations

from solution_intelligence.embeddings import LocalEmbedder
from solution_intelligence.models import (
    KnowledgeEntry,
    RetrievedSolution,
)


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
    """Attaches a confidence score to retrieved solutions.

    Confidence blends retrieval similarity with the entry's historical
    success rate and how well it is documented.
    """

    def score(self, entry: KnowledgeEntry, similarity: float) -> float:
        """Return a composite 0..1 confidence score."""
        success = entry.success_rate
        doc_coverage = _documentation_coverage(entry)
        base = 0.55 * success + 0.25 * doc_coverage + 0.20 * similarity
        return round(min(1.0, max(0.0, base)), 3)


def _documentation_coverage(entry: KnowledgeEntry) -> float:
    """Estimate how complete an entry's documentation is."""
    parts = [entry.title, entry.description, entry.resolution]
    non_empty = sum(1 for p in parts if p.strip())
    return non_empty / len(parts)
