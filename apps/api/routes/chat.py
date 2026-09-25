"""Conversational agent endpoints (start + respond)."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter

from apps.api.engine_cache import get_or_build_engine
from apps.api.models import (
    ChatRespondRequest,
    ChatResponse,
    ChatStartRequest,
    ChatTurn,
    IncidentContext,
    NextBestAction,
    RetrievedSolution,
)
from apps.api.policy import (
    CHAT_SCORE_BOOST,
    evaluate_policy,
    to_next_best_action,
)

from apps.api.views import SOURCE_LABELS
from apps.api.why import attach_why
from solution_intelligence.policy import (
    ABSTAIN_THRESHOLD,
    CONFIDENT_THRESHOLD,
)
from solution_intelligence.retrieval import IncidentContext as CoreContext

router = APIRouter(tags=["chat"])


def _to_context(req: IncidentContext | None) -> CoreContext | None:
    """Convert a request context into the engine's core context model."""
    if req is None:
        return None
    return CoreContext(
        error_code=req.error_code,
        module=req.module,
        environment=req.environment,
    )


def _now() -> str:
    """Current local time formatted HH:MM AM/PM."""
    return datetime.now().strftime("%I:%M %p").lstrip("0")


# Chat display multiplier: conversational queries are wordier than ticket
# text, so raw cosine similarity under-reports genuinely good matches. Boost
# the displayed score to keep it consistent with the Find a Solution page.
# The constant lives in apps.api.policy next to the abstain policy so the
# policy is evaluated on the same displayed number the user sees.
_CHAT_SCORE_BOOST = CHAT_SCORE_BOOST

# Reply bands on the boosted display scale. The thresholds are the shared
# abstain policy's (solution_intelligence.policy) so Find, Chat, and the
# eval framework all abstain at exactly the same confidence.
_CHAT_LOW_CONFIDENCE_THRESHOLD = ABSTAIN_THRESHOLD
_CHAT_CONFIDENT_THRESHOLD = CONFIDENT_THRESHOLD


def _display_score(h) -> float:
    """Return the chat-display score, boosted and capped at 1.0."""
    return round(min(1.0, h.combined_score * _CHAT_SCORE_BOOST), 3)


def _hits_to_solutions(
    hits,
    all_entries: list | None = None,
    context=None,
) -> list[RetrievedSolution]:
    all_entries = all_entries if all_entries is not None else []
    return [
        RetrievedSolution(
            id=h.entry.id,
            title=h.entry.title,
            source=str(SOURCE_LABELS.get(h.entry.source_type, h.entry.source_type)),
            category=h.entry.category,
            score=_display_score(h),
            confidence=round(h.confidence, 3),
            description=h.entry.description,
            resolution=h.entry.resolution,
            date=h.entry.date or "\u2014",
            language=h.entry.language or "en",
            english_title=h.entry.english_title,
            english_description=h.entry.english_description,
            english_resolution=h.entry.english_resolution,
            **attach_why(h, all_entries, context=context),
        )
        for h in hits
    ]


def _build_assistant_turn(
    query: str,
    candidates: list[RetrievedSolution],
    next_best_action: NextBestAction | None = None,
    rejected_titles: list[str] | None = None,
) -> str:
    """Compose a deterministic assistant reply from the current candidates.

    The caller passes the same ``next_best_action`` the banner renders, so the
    prose and the guidance can never disagree: when a next-best action is
    present, the policy already declined to offer a fix, and the reply says so
    instead of presenting a look-alike as the best answer.

    ``rejected_titles`` names the records the user ruled out in this message,
    so the reply can say what it eliminated and moved on to, rather than
    silently swapping the answer.
    """
    ruled_out = ""
    if rejected_titles:
        named = ", ".join(rejected_titles[:2])
        ruled_out = f"Ruling that out: {named}."

    if not candidates or next_best_action is not None:
        if next_best_action is not None:
            # The banner names the record it judged, and the cards below the
            # reply list it, so the prose stays clean and the two surfaces
            # cannot disagree. "Here is the next best match instead" belongs
            # only on the path that actually offers one.
            if ruled_out:
                return f"{next_best_action.message} {ruled_out}"
            return next_best_action.message
        return (
            "I couldn't find an appropriate match in the available records for "
            "that. Try describing the issue differently, or escalate to a "
            "subject-matter expert."
        )
    top = candidates[0]
    ruled_out = f"{ruled_out} Here is the next best match instead." if ruled_out else ""
    intro = (
        f"According to the available documentation, the best answer is **{top.title}**."
    )
    steps = top.resolution.strip()
    # The counts stay alongside the plain sentence: "9 of 9" is concrete
    # evidence a business audience trusts, and unlike a percentage it cannot
    # be misread as a probability.
    evidence = (
        f"Track record: worked {top.worked} of {top.attempted} times."
        if top.attempted > 0
        else ""
    )
    return "\n\n".join(
        part
        for part in (
            intro,
            f"**How to fix it**\n{steps}" if steps else None,
            top.confidence_note or None,
            evidence or None,
            ruled_out or None,
        )
        if part
    )


@router.post("/api/chat/start", response_model=ChatResponse)
async def chat_start(req: ChatStartRequest) -> ChatResponse:
    """Start a new chat session with the engine agent."""
    engine = get_or_build_engine(0)
    context = _to_context(req.context)
    session = engine.agent.start(req.session_id, req.query, context=context)
    # The agent already returns the order it presents, so the session's
    # top candidate and the card the user sees are the same record.
    core_hits = session.turns[-1].candidates if session.turns else []
    candidates = (
        _hits_to_solutions(
            core_hits,
            all_entries=engine.index.entries,
            context=context,
        )
        if session.turns
        else []
    )
    verdict = evaluate_policy(core_hits, context, query=req.query, surface="chat")
    reply = _build_assistant_turn(
        req.query, candidates, next_best_action=to_next_best_action(verdict)
    )
    session.add_system(reply)
    turns: list[ChatTurn] = [
        ChatTurn(role="user", text=req.query, timestamp=_now()),
        ChatTurn(role="assistant", text=reply, timestamp=_now()),
    ]
    return ChatResponse(
        turns=turns,
        candidates=candidates,
        next_best_action=to_next_best_action(verdict),
    )


@router.post("/api/chat/respond", response_model=ChatResponse)
async def chat_respond(req: ChatRespondRequest) -> ChatResponse:
    """Send a follow-up message within an existing chat session."""
    engine = get_or_build_engine(0)
    rejected_titles_before: list[str] = []
    if req.session_id in engine.agent.sessions:
        rejected_titles_before = list(
            engine.agent.sessions[req.session_id].rejected_titles
        )
    if req.session_id not in engine.agent.sessions:
        session = engine.agent.start(req.session_id, req.message)
    else:
        session = engine.agent.respond(req.session_id, req.message)
    core_hits = session.turns[-1].candidates
    candidates = _hits_to_solutions(
        core_hits, all_entries=engine.index.entries, context=session.context
    )
    verdict = evaluate_policy(
        core_hits,
        session.context,
        query=f"{session.query} {req.message}",
        surface="chat",
    )
    # Records ruled out by this very message, so the reply can name them.
    # The titles come from the session because a rejected record is already
    # demoted out of the candidate list by the time we get here.
    titles_before = rejected_titles_before
    newly_rejected = [
        title for title in session.rejected_titles if title not in titles_before
    ]
    reply = _build_assistant_turn(
        req.message,
        candidates,
        next_best_action=to_next_best_action(verdict),
        rejected_titles=newly_rejected,
    )
    session.add_system(reply)
    turns: list[ChatTurn] = []
    for t in session.turns:
        if t.role == "user":
            turns.append(ChatTurn(role="user", text=t.text, timestamp=_now()))
    turns.append(ChatTurn(role="assistant", text=reply, timestamp=_now()))
    return ChatResponse(
        turns=turns,
        candidates=candidates,
        next_best_action=to_next_best_action(verdict),
    )
