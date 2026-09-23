"""Outcome-aware ranking tests for the shared retrieval path.

Covers the issue #15 acceptance criteria: a repeatedly-failed fix must
never outrank a proven one despite higher raw similarity, ranking ties
must resolve deterministically, and the chat agent must rank through the
same shared path as Find a Solution.
"""

import re

from solution_intelligence.agent import ConversationalAgent
from solution_intelligence.embeddings import LocalEmbedder
from solution_intelligence.models import KnowledgeEntry
from solution_intelligence.retrieval import (
    IncidentContext,
    KnowledgeIndex,
    rank_results,
)

_QUERY = "vpn connection dropping"

_VOCAB = (
    "vpn",
    "connection",
    "dropping",
    "in",
    "the",
    "office",
    "invoice",
    "used",
    "wrong",
    "tax",
    "code",
    "restore",
    "last",
    "nightly",
    "database",
    "snapshot",
)


_EMBED_DIMS = 16
_UNITS: dict[str, list[float]] = {
    word: [1.0 if i == pos else 0.0 for i in range(_EMBED_DIMS)]
    for pos, word in enumerate(_VOCAB)
}


class ScriptedEmbedder(LocalEmbedder):
    """Deterministic toy embedder for ranking tests.

    Maps vocabulary words to fixed unit vectors and embeds a text as the
    normalized sum of its word vectors, so similarity is fully predictable
    without loading the real (slow) sentence-transformer model.
    """

    def embed(self, text: str, for_query: bool = False) -> list[float]:
        acc = [0.0] * _EMBED_DIMS
        for word in re.findall(r"[a-z0-9]+", text.lower()):
            unit = _UNITS.get(word)
            if unit is not None:
                acc = [a + u for a, u in zip(acc, unit)]
        norm = sum(x * x for x in acc) ** 0.5 or 1.0
        return [x / norm for x in acc]

    def similarity(self, a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        return max(0.0, min(1.0, dot))


def make_entry(entry_id: str, title: str, worked: tuple[int, int]) -> KnowledgeEntry:
    return KnowledgeEntry(
        id=entry_id,
        source_type="ticket",
        title=title,
        description="",
        resolution="",
        worked_count=worked,
    )


def _ranking_index() -> KnowledgeIndex:
    """Index where the failed fix is MORE similar to the query.

    The FAILED record shares the query terms plus two filler words; PROVEN
    shares the same query terms plus three, so raw similarity ranks FAILED
    first (~0.707 vs ~0.655). Only the outcome-aware confidence (0/20
    attempts worked vs 19/20) can put PROVEN on top.
    """
    index = KnowledgeIndex(embedder=ScriptedEmbedder())
    index.add(
        make_entry(
            "FAILED",
            "vpn connection dropping in the office",
            worked=(0, 20),
        )
    )
    index.add(
        make_entry(
            "PROVEN",
            "vpn connection dropping after the database snapshot restore",
            worked=(19, 20),
        )
    )
    return index


def test_failed_fix_loses_to_proven_despite_higher_similarity():
    index = _ranking_index()
    results = rank_results(index, _QUERY, top_k=2)
    assert [r.entry.id for r in results] == ["PROVEN", "FAILED"]
    assert results[0].confidence > results[1].confidence
    assert results[0].score < results[1].score  # raw similarity stays visible


def test_equal_confidence_resolves_by_entry_id():
    index = KnowledgeIndex(embedder=ScriptedEmbedder())
    index.add(make_entry("T-B", "alpha vpn connection dropping", worked=(4, 4)))
    index.add(make_entry("T-A", "bravo vpn connection dropping", worked=(4, 4)))
    results = rank_results(index, _QUERY, top_k=2)
    assert [r.entry.id for r in results] == ["T-A", "T-B"]


def test_agent_ranks_through_shared_path():
    index = _ranking_index()
    proven = index.get("PROVEN")
    assert proven is not None
    proven.error_code = "E-1337"
    agent = ConversationalAgent(index)
    context = IncidentContext(error_code="E-1337")
    session = agent.start("s1", _QUERY, context=context)
    candidates = session.turns[0].candidates
    assert [c.entry.id for c in candidates] == ["PROVEN", "FAILED"]
    # Matched-signal metadata is attached only by the shared ranking path;
    # the pre-issue-15 agent path left it empty.
    assert candidates[0].signals == ["error_code"]

    session = agent.respond("s1", "more options please")
    ids = [c.entry.id for c in session.turns[-1].candidates]
    assert ids == ["PROVEN", "FAILED"]
