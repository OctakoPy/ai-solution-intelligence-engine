"""Deterministic evidence builders for the trust-first "WHY THIS" panel.

Both the search and the chat endpoints translate core retrieval hits into
API payloads through :func:`attach_why`, so the evidence panel is identical
on every surface: the same hit always carries the same per-signal score
breakdown, prior-success counts, supporting records, and caveats.

Everything here is rule-based synthesis over indexed data — no external LLM
calls — keeping the demo stance that every number and sentence on the panel
is auditable and reproducible.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from apps.api.models import EvidenceRecord
from apps.api.views import SOURCE_LABELS

if TYPE_CHECKING:
    from solution_intelligence.models import KnowledgeEntry, RetrievedSolution


def _source_label(source_type: str) -> str:
    """Human-readable source-system name for an entry."""
    return SOURCE_LABELS.get(source_type, source_type)


def _build_evidence(
    hit: RetrievedSolution,
    all_entries: list[KnowledgeEntry],
) -> list[EvidenceRecord]:
    """Collect supporting records for a hit, self first.

    The hit itself carries its own outcome history; records in the same
    ``duplicate_group`` (same issue seen across source systems) back it up.
    Output is deterministic: self first, then peers ordered by entry id.
    """
    evidence = [
        EvidenceRecord(
            id=hit.entry.id,
            title=hit.entry.title,
            source=_source_label(hit.entry.source_type),
            date=hit.entry.date or "",
            worked=hit.entry.worked,
            attempted=hit.entry.attempted,
        )
    ]
    group = hit_entry_group(all_entries, hit.entry.id)
    if group:
        for entry in all_entries:
            if entry.id == hit.entry.id or entry.duplicate_group != group:
                continue
            evidence.append(
                EvidenceRecord(
                    id=entry.id,
                    title=entry.title,
                    source=_source_label(entry.source_type),
                    date=entry.date or "",
                    worked=entry.worked,
                    attempted=entry.attempted,
                )
            )
    return evidence


def hit_entry_group(
    all_entries: list[KnowledgeEntry],
    entry_id: str,
) -> str | None:
    """Return the duplicate-group id of an indexed entry, if any."""
    for entry in all_entries:
        if entry.id == entry_id:
            return entry.duplicate_group
    return None


def _build_caveats(
    hit: RetrievedSolution,
    all_entries: list[KnowledgeEntry],
) -> list[str]:
    """Rule-based caveats for a hit, in a fixed order."""
    caveats: list[str] = []
    group = hit_entry_group(all_entries, hit.entry.id)
    if group is None:
        caveats.append(
            "Unverified record: no linked recurrence in another source "
            "system corroborates this fix yet."
        )
    if hit.entry.attempted == 0:
        caveats.append(
            "No confirmed outcomes yet: this record has never been marked "
            "worked or failed, so its history is unknown."
        )
    return caveats


def attach_why(
    hit: RetrievedSolution,
    all_entries: list[KnowledgeEntry],
) -> dict:
    """Build the why-panel payload fields for one retrieval hit.

    Returns keyword arguments for the API ``RetrievedSolution`` schema:
    the per-signal breakdown, prior-success counts, supporting evidence
    records, and caveats. Pure function of the hit and the index contents.
    """
    return {
        "signal_breakdown": {k: round(v, 4) for k, v in hit.signal_breakdown.items()},
        "worked": hit.entry.worked,
        "attempted": hit.entry.attempted,
        "evidence": _build_evidence(hit, all_entries),
        "caveats": _build_caveats(hit, all_entries),
    }
