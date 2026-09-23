"""The one abstain policy shared by every surface.

"Knows when not to guess": when evidence is weak, the engine changes the
action instead of inventing certainty. This module is the single source of
truth for that behavior — the same thresholds decide, for the same hit,
whether Find a Solution, Chat, and the raw API present a confident fix or
a next-best action.

The values live here (not in chat, not in eval) so the pilot evaluation in
:mod:`solution_intelligence.evaluate` and the API layer can mirror exactly
what the demo shows, and so tuning the policy is a one-line change.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from solution_intelligence.models import KnowledgeEntry, RetrievedSolution
from solution_intelligence.retrieval import IncidentContext

# Below this the engine abstains from offering a fix at all: it shows
# look-alikes only as starting points and returns a next-best action.
ABSTAIN_THRESHOLD = 0.75
# At or above this the engine answers confidently (chat wording band).
CONFIDENT_THRESHOLD = 0.90
# Below this similarity the engine does not trust the match even if
# the record's history is perfect — the score says the query is not
# really about this record, so the banner still appears.
PROVEN_FLOOR = 0.35
# A record that has worked every time (with enough attempts) is a go
# regardless of composite confidence. Abstain is for genuinely
# weak / unproven matches.
PROVEN_MIN_ATTEMPTS = 3

Action = Literal["ask_context", "escalate_sme", "proceed"]


def is_proven(top: RetrievedSolution | None) -> bool:
    """True when this hit has worked every time it was tried.

    Used to bypass the abstain banner for proven fixes whose
    composite confidence happens to be low (e.g. a strong match
    strength with no structured context). A record needs a real
    track record before we trust it enough to skip escalate.
    """
    if top is None or top.entry is None:
        return False
    attempted = top.entry.attempted
    if attempted < PROVEN_MIN_ATTEMPTS:
        return False
    return top.entry.worked >= attempted


@dataclass(frozen=True)
class PolicyVerdict:
    """The abstain decision for one retrieval result.

    ``action`` is one of:

    * ``proceed``        — confidence at or above the confident band.
    * ``ask_context``    — middle band: offer nearest matches but ask for
      missing structured context (error code / module / environment).
    * ``escalate_sme``   — below the abstain threshold: do not offer a fix,
      hand off to a subject-matter expert.

    ``next_best_action`` carries the user-facing payload for the second and
    third cases and is ``None`` when the engine proceeds.
    """

    action: Action
    next_best_action: dict[str, Any] | None = None


def decide(
    top: RetrievedSolution | None,
    *,
    context: IncidentContext | None = None,
    abstain_threshold: float = ABSTAIN_THRESHOLD,
    confident_threshold: float = CONFIDENT_THRESHOLD,
) -> PolicyVerdict:
    """Apply the shared abstain policy to a retrieval result.

    Args:
        top: The highest-ranked candidate (``None`` when nothing matched).
        context: Optional structured incident context; used to ask for the
            specific missing fields rather than generic "more detail".
        abstain_threshold: Below this confidence the engine escalates.
        confident_threshold: At or above this the engine proceeds.

    Returns:
        A :class:`PolicyVerdict` whose payload is deterministic for a given
        result, so the same query always produces the same guidance.
    """
    confidence = top.confidence if top is not None else 0.0
    if confidence >= confident_threshold:
        return PolicyVerdict(action="proceed")
    if confidence >= abstain_threshold:
        return PolicyVerdict(
            action="ask_context",
            next_best_action=_ask_context_payload(top, context),
        )
    if is_proven(top) and confidence >= PROVEN_FLOOR:
        return PolicyVerdict(action="proceed")
    return PolicyVerdict(
        action="escalate_sme",
        next_best_action=_escalate_payload(top),
    )


def _ask_context_payload(
    top: RetrievedSolution | None,
    context: IncidentContext | None,
) -> dict[str, Any]:
    """Build the ask-for-context next-best-action payload."""
    missing: list[str] = []
    if context is None or not (context.error_code or "").strip():
        missing.append("error_code")
    if context is None or not (context.module or "").strip():
        missing.append("module")
    if context is None or not (context.environment or "").strip():
        missing.append("environment")
    if missing:
        fields = ", ".join(m.replace("_", " ") for m in missing)
        message = (
            "Not confident enough to recommend a fix. Confirm the "
            f"{fields} of the incident, then search again."
        )
    else:
        # Context is complete yet confidence is still mid-band: do not ask
        # again for fields the user already supplied.
        message = (
            "Not confident enough to recommend a fix, even with the full "
            "incident context. Review the nearest matches with a "
            "specialist before applying anything."
        )
    return {
        "action": "ask_context",
        "message": message,
        "missing_fields": missing,
    }


def _escalate_payload(top: RetrievedSolution | None) -> dict[str, Any]:
    """Build the escalate-to-SME next-best-action payload."""
    nearest: dict[str, str] | None = None
    if top is not None:
        nearest = {"id": top.entry.id, "title": top.entry.title}
        best = round(top.confidence * 100)
        message = (
            "No historical record is a confident match (best: "
            f"{best}%). Escalate to a subject-matter expert instead of "
            "applying a guess."
        )
    else:
        message = (
            "No matching historical record exists for this issue. Escalate "
            "to a subject-matter expert for manual handling."
        )
    return {"action": "escalate_sme", "message": message, "nearest_record": nearest}


def _normalize(value: str | None) -> str:
    """Lower-case, trimmed form used for match comparisons."""
    return (value or "").strip().lower()


def mismatched_signals(
    entry: KnowledgeEntry,
    context: IncidentContext | None,
) -> list[str]:
    """Names of the structured context signals that positively mismatched.

    The complement of ``matched_signals``: a signal is listed here when the
    incident *supplied* that field, the record has one too, and they do not
    agree. This is the context-trap detector — a shared error code with a
    different environment usually means a different root cause, so the hit
    must carry a "verify root cause" caveat rather than looking like an
    answer.
    """
    signals: list[str] = []
    if context is None:
        return signals
    if (
        context.error_code
        and entry.error_code
        and _normalize(entry.error_code) != _normalize(context.error_code)
    ):
        signals.append("error_code")
    if (
        context.module
        and entry.module
        and not _module_overlaps(entry.module, context.module)
    ):
        signals.append("module")
    if (
        context.environment
        and entry.environment
        and _normalize(entry.environment) != _normalize(context.environment)
    ):
        signals.append("environment")
    return signals


def _module_overlaps(entry_module: str, incident_module: str) -> bool:
    """True when incident and record modules share at least one token."""
    incident_terms = set(incident_module.lower().split())
    entry_terms = set(entry_module.lower().split())
    if not incident_terms or not entry_terms:
        return False
    return bool(incident_terms & entry_terms)


def is_context_trap(
    hit: RetrievedSolution,
    context: IncidentContext | None,
) -> bool:
    """True when a hit matches strongly on one cue but conflicts elsewhere.

    The canonical trap: the same error code on a different environment
    (PROD vs UAT) is a different root cause. Requiring at least one match
    plus at least one mismatch keeps genuinely unrelated records (which
    simply match nothing) out of the trap state.
    """
    matched = getattr(hit, "signals", None) or []
    return bool(matched) and bool(mismatched_signals(hit.entry, context))
