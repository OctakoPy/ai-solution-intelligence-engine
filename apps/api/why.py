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
from solution_intelligence.policy import is_context_trap, mismatched_signals

if TYPE_CHECKING:
    from solution_intelligence.models import KnowledgeEntry, RetrievedSolution
    from solution_intelligence.retrieval import IncidentContext


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


# Context-trap warning: same error code, different environment (or any
# matched cue contradicted elsewhere) usually means a different root cause.
_CONTEXT_TRAP_CAVEAT = (
    "Verify root cause before applying: this record matches part of your "
    "incident context but conflicts on {fields} — evidence may be from a "
    "different context."
)


def _build_caveats(
    hit: RetrievedSolution,
    all_entries: list[KnowledgeEntry],
    context: IncidentContext | None = None,
) -> list[str]:
    """Rule-based caveats for a hit, in a fixed order."""
    caveats: list[str] = []
    group = hit_entry_group(all_entries, hit.entry.id)
    if group is None:
        caveats.append(
            "Seen in one system only so far — no second source has logged "
            "this problem yet, so there is nothing to cross-check it against."
        )
    if hit.entry.attempted == 0:
        caveats.append(
            "No confirmed outcomes yet: this record has never been marked "
            "worked or failed, so its history is unknown."
        )
    if is_context_trap(hit, context):
        mismatched = mismatched_signals(hit.entry, context)
        fields = " / ".join(m.replace("_", " ") for m in mismatched)
        caveats.append(_CONTEXT_TRAP_CAVEAT.format(fields=fields))
    return caveats


def confidence_note(hit: RetrievedSolution) -> str:
    """One plain sentence saying why this record can be trusted.

    A business audience always asks why a record that "worked 8 of 8" is
    shown at a middling percentage. The honest answer is the reasons, not a
    figure: the composite score is a weighted blend, and a bare number invites
    reading it as a probability of success. Naming the evidence answers the
    question directly and keeps the wording identical on Find and Chat.
    """
    entry = hit.entry
    worked, attempted = entry.worked, entry.attempted
    perfect = attempted > 0 and worked == attempted
    strong = attempted > 0 and (worked / attempted) >= 0.8
    exact = "error_code" in (getattr(hit, "signals", None) or [])

    if perfect and exact:
        return (
            "High confidence - the error code matches exactly, and this fix "
            "has worked every time it was tried."
        )
    if perfect:
        return "High confidence - this fix has worked every time it was tried."
    if strong and exact:
        return "Good confidence - the error code matches, and this fix usually works."
    if strong:
        return "Good confidence - this fix has usually worked."
    if attempted == 0:
        return "Worth reviewing - this is a related record with no outcome history yet."
    return "Worth reviewing - this is a related record, not a confirmed match."


def attach_why(
    hit: RetrievedSolution,
    all_entries: list[KnowledgeEntry],
    context: IncidentContext | None = None,
) -> dict:
    """Build the why-panel payload fields for one retrieval hit.

    Returns keyword arguments for the API ``RetrievedSolution`` schema:
    the per-signal breakdown, prior-success counts, supporting evidence
    records, caveats, and the plain-language confidence note. Pure function of
    the hit and the index contents.
    """
    return {
        "signal_breakdown": {k: round(v, 4) for k, v in hit.signal_breakdown.items()},
        "worked": hit.entry.worked,
        "attempted": hit.entry.attempted,
        "evidence": _build_evidence(hit, all_entries),
        "caveats": _build_caveats(hit, all_entries, context=context),
        "confidence_note": confidence_note(hit),
    }
