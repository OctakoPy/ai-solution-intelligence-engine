"""API-side mapping of the shared abstain policy to response payloads.

The policy decision itself lives in :mod:`solution_intelligence.policy`
(single source of truth for thresholds and wording); this module only
translates a :class:`PolicyVerdict` into the ``NextBestAction`` schema the
API returns on both ``/api/search`` and ``/api/chat``.
"""

from __future__ import annotations

from typing import Any

from apps.api.models import NextBestAction
from solution_intelligence.models import RetrievedSolution
from solution_intelligence.policy import PolicyVerdict

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


def evaluate_policy(
    hits: list[RetrievedSolution],
    context: Any,
) -> PolicyVerdict:
    """Run the shared policy over a hit list using the chat display scale.

    Chat displays ``combined_score * _CHAT_SCORE_BOOST`` (see
    ``routes/chat.py``); Find shows the confidence directly. Applying the
    policy on the *displayed* number keeps both surfaces consistent with
    what the user actually sees: when the UI shows below-band percentages,
    the payload carries a next-best action.
    """
    from solution_intelligence.policy import decide

    from apps.api.routes.chat import _CHAT_SCORE_BOOST

    top = hits[0] if hits else None
    if top is None:
        return decide(None, context=context)
    displayed = min(1.0, top.combined_score * _CHAT_SCORE_BOOST)
    scaled = RetrievedSolution(
        entry=top.entry,
        score=top.score,
        confidence=displayed,
    )
    return decide(scaled, context=context)
