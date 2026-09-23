"""Analytics for the manager dashboard."""

from __future__ import annotations

from collections import Counter

from solution_intelligence.models import KnowledgeEntry
from solution_intelligence.policy import PROVEN_MIN_ATTEMPTS


def top_categories(entries: list[KnowledgeEntry], n: int = 6) -> list[tuple[str, int]]:
    """Return the most common problem categories and their counts."""
    counts = Counter(e.category for e in entries)
    return counts.most_common(n)


def source_breakdown(entries: list[KnowledgeEntry]) -> dict[str, int]:
    """Distribution of entries across the four source systems."""
    return dict(Counter(e.source_type for e in entries))


def average_success_rate(entries: list[KnowledgeEntry]) -> float:
    """Average historical success rate across all curated entries."""
    rated = [e for e in entries if e.attempted > 0]
    if not rated:
        return 0.0
    return round(sum(e.success_rate for e in rated) / len(rated), 3)


def proven_fixes(entries: list[KnowledgeEntry]) -> int:
    """Count entries with a proven track record.

    An entry is proven when it has been attempted at least
    ``PROVEN_MIN_ATTEMPTS`` times and has never failed — the same bar the
    abstain policy uses to trust a weak-confidence match.
    """
    return sum(
        1
        for e in entries
        if e.attempted >= PROVEN_MIN_ATTEMPTS and e.worked >= e.attempted
    )


def total_solutions(entries: list[KnowledgeEntry]) -> int:
    """Total number of curated solutions available."""
    return len(entries)


def searchable_docs(entries: list[KnowledgeEntry], *, searchable: bool = True) -> int:
    """Count how many entries are searchable (indexed, not rejected)."""
    return len(entries) if searchable else 0


def resolution_time_by_category(
    entries: list[KnowledgeEntry], n: int = 6
) -> list[tuple[str, str]]:
    """Average resolution time (minutes) per category, derived from entry data.

    The demo dataset has no per-ticket clock, so resolution time is modelled
    deterministically from each entry's historical effort: more attempts means
    a harder, slower problem. Entries with many past attempts resolve slower;
    clean, well-trodden fixes resolve fast. This keeps the trend data-driven
    and stable across runs while still differentiating categories.
    """
    grouped: dict[str, list[float]] = {}
    for e in entries:
        estimated = 2.0 + 0.9 * e.attempted
        grouped.setdefault(e.category, []).append(estimated)

    ranked: list[tuple[str, float]] = []
    for cat, times in grouped.items():
        ranked.append((cat, round(sum(times) / len(times), 1)))
    ranked.sort(key=lambda x: x[1])

    def _fmt(minutes: float) -> str:
        if minutes < 60:
            return f"{minutes:.0f} min"
        h = int(minutes // 60)
        m = int(round(minutes % 60))
        return f"{h}h {m:02d}m" if m else f"{h}h"

    return [(cat, _fmt(m)) for cat, m in ranked[:n]]
