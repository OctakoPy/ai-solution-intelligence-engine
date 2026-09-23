"""API-side mapping of the shared abstain policy to response payloads.

The policy decision itself lives in :mod:`solution_intelligence.policy`
(single source of truth for thresholds and wording); this module only
translates a :class:`PolicyVerdict` into the ``NextBestAction`` schema the
API returns on both ``/api/search`` and ``/api/chat``.

One invariant rules this module: **guidance matches the displayed number.**
Each surface passes the score it actually shows the user (Find shows the
outcome-aware confidence; Chat boosts similarity into its display scale),
and the policy verdict is computed from that, so a result displayed at 84%
never carries a "not confident" banner while a 51% one carries none.
"""

from __future__ import annotations

from typing import Any

from apps.api.models import NextBestAction
from solution_intelligence.models import RetrievedSolution
from solution_intelligence.policy import PolicyVerdict, decide

# Chat display multiplier: conversational queries are wordier than ticket
# text, so raw cosine similarity under-reports genuinely good matches. The
# constant lives here next to the abstain policy so the policy is evaluated
# on the same displayed number the user sees.
CHAT_SCORE_BOOST = 1.25


def to_next_best_action(verdict: PolicyVerdict) -> NextBestAction | None:
    """Map a core policy verdict to the API payload, or ``None`` to proceed."""
    nba = verdict.next_best_action
    if verdict.action == "proceed" or nba is None:
        return None
    nearest = nba.get("nearest_record")
    return NextBestAction(
        action=nba["action"],  # type: ignore[literal-required]
        message=nba["message"],
        missing_fields=list(nba.get("missing_fields", [])),
        nearest_record_id=nearest["id"] if nearest else None,
        nearest_record_title=nearest["title"] if nearest else None,
    )


def _displayed_confidence(
    hit: RetrievedSolution,
    surface: str,
) -> float:
    """The confidence the given surface actually shows for this hit."""
    if surface == "chat":
        return min(1.0, hit.combined_score * CHAT_SCORE_BOOST)
    # Find a Solution (and the raw API) display the outcome-aware
    # confidence directly.
    return hit.confidence


def evaluate_policy(
    hits: list[RetrievedSolution],
    context: Any,
    *,
    surface: str = "find",
) -> PolicyVerdict:
    """Run the shared policy over a hit list for one surface.

    Args:
        hits: Ranked candidates from the shared ranking path.
        context: Structured incident context, if the user supplied any.
        surface: ``"find"`` or ``"chat"`` — determines which displayed
            score the policy is evaluated against.

    Returns:
        The :class:`PolicyVerdict` computed from the displayed confidence
        of the top hit, so guidance and UI always agree.
    """
    top = hits[0] if hits else None
    if top is None:
        return decide(None, context=context)
    displayed = _displayed_confidence(top, surface)
    scaled = RetrievedSolution(
        entry=top.entry,
        score=top.score,
        confidence=displayed,
    )
    return decide(scaled, context=context)
