"""Helpers to translate backend models into API view payloads."""

from __future__ import annotations

from collections import OrderedDict

from solution_intelligence.models import PipelineStep, StageResult

SOURCE_ICONS: dict[str, str] = {
    "ticket": "\U0001f39f\ufe0f",  # 🎟️
    "sap_note": "\U0001f5c4\ufe0f",  # 🗄️
    "sharepoint_doc": "\U0001f4c1",  # 📁
    "kb_article": "\U0001f4da",  # 📚
}

SOURCE_LABELS: dict[str, str] = {
    "ticket": "Ticketing System",
    "sap_note": "SAP System",
    "sharepoint_doc": "SharePoint",
    "kb_article": "Knowledge Base",
}

STAGE_NAMES: dict[str, str] = {
    "stage1": "Stage 1 \u00b7 Structural",
    "judge": "AI Judge \u00b7 Quality",
    "duplicate": "Duplicate \u00b7 Similarity",
}


def _verdict_reason(checks: list[PipelineStep], outcome: str) -> str:
    """Pick a human-readable verdict reason for a record."""
    if outcome == "rejected":
        for step in checks:
            if step.result == StageResult.REJECT:
                return step.label
        return "Failed a quality gate"
    if outcome == "flagged":
        for step in checks:
            if step.result == StageResult.FLAG:
                return step.label
        return "Flagged for human review"
    remarks = [s.label for s in checks if s.stage in ("judge", "duplicate")]
    return remarks[-1] if remarks else "Passed all quality gates"


def build_views(run) -> list[dict]:
    """Group pipeline steps by record and attach a verdict."""
    groups: OrderedDict[str, list[PipelineStep]] = OrderedDict()
    for step in run.steps:
        groups.setdefault(step.entry.id, []).append(step)

    added = {e.id for e in run.ingested}
    # Near-duplicates are ingested (kept visible for the demo) but never
    # indexed, so they surface as "flagged" rather than "added".
    flagged = {step.entry.id for step in run.steps if step.result == StageResult.FLAG}
    views: list[dict] = []
    for entry_id, checks in groups.items():
        entry = checks[0].entry
        if entry_id in added and entry_id in flagged:
            outcome = "flagged"
        elif entry_id in added:
            outcome = "added"
        else:
            outcome = "rejected"
        checks_payload: list[dict] = []
        for step in checks:
            if step.stage == "source":
                continue
            checks_payload.append(
                {
                    "stage": step.stage,
                    "label": STAGE_NAMES.get(step.stage, step.stage),
                    "result": step.result.value,
                    "score": step.score,
                    "detail": step.label,
                }
            )
        views.append(
            {
                "id": entry_id,
                "source_type": entry.source_type,
                "source_icon": SOURCE_ICONS.get(entry.source_type, "\U0001f5c2\ufe0f"),
                "source_label": SOURCE_LABELS.get(entry.source_type, entry.source_type),
                "title": entry.title,
                "category": entry.category,
                "date": entry.date or "\u2014",
                "description": entry.description or "",
                "resolution": entry.resolution or "",
                "outcome": outcome,
                "reason": _verdict_reason(checks, outcome),
                "checks": checks_payload,
                "language": entry.language or "en",
            }
        )
    return views
