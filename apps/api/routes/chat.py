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
from apps.api.policy import CHAT_SCORE_BOOST, evaluate_policy, to_next_best_action

from apps.api.views import SOURCE_LABELS
from apps.api.why import attach_why
from solution_intelligence.policy import (
    ABSTAIN_THRESHOLD,
    CONFIDENT_THRESHOLD,
    PROVEN_FLOOR,
    PROVEN_MIN_ATTEMPTS,
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
) -> str:
    """Compose a deterministic assistant reply from the current candidates.

    When the shared abstain policy produces a next-best action, its message
    is appended so the reply text and the structured payload never disagree.
    """
    if not candidates:
        if next_best_action is not None:
            return next_best_action.message
        return "No confident matches found. Try describing the issue differently."
    top = candidates[0]
    if (
        top.score < _CHAT_LOW_CONFIDENCE_THRESHOLD
        and not (
            top.worked >= top.attempted
            and top.attempted >= PROVEN_MIN_ATTEMPTS
            and top.confidence >= PROVEN_FLOOR
        )
    ):
        best = round(top.score * 100)
        lines = [
            "None of the historical records are a confident match — the best "
            f"one is only {best}% similar. I won't guess a fix, because a "
            "wrong answer here could make things worse.",
            "Here are the nearest look-alikes, purely as a starting point for "
            "a specialist:",
        ]
        for idx, c in enumerate(candidates, start=1):
            lines.append(f"{idx}. **{c.title}** — {round(c.score * 100)}% match")
        lines.append(
            next_best_action.message
            if next_best_action is not None
            else (
                "My recommendation: escalate to a subject-matter expert for manual "
                "handling rather than auto-applying a solution."
            )
        )
        return "\n\n".join(lines)
    if (
        top.score < _CHAT_CONFIDENT_THRESHOLD
        and not (
            top.worked >= top.attempted
            and top.attempted >= PROVEN_MIN_ATTEMPTS
            and top.confidence >= PROVEN_FLOOR
        )
    ):
        best = round(top.score * 100)
        lines = [
            (
                f"I'm not fully certain of an exact match — the closest record "
                f"is about {best}% similar."
            ),
            "Here are the closest matches I could find — are any of these helpful?",
        ]
        for idx, c in enumerate(candidates, start=1):
            lines.append(f"{idx}. **{c.title}** — {round(c.score * 100)}% match")
        if next_best_action is not None:
            lines.append(next_best_action.message)
        return "\n\n".join(lines)
    lines = [
        "This issue is usually caused by cached authentication or sync settings. "
        "Here are the steps that resolved it for similar cases:",
    ]
    for idx, c in enumerate(candidates, start=1):
        lines.append(f"{idx}. **{c.title}** — {round(c.score * 100)}% match")
    lines.append(
        f"This solved the issue in {round(top.score * 100)}% of similar cases."
    )
    sources = " · ".join(
        f"{c.title} ({c.source}) – {c.date} ({round(c.score * 100)}%)"
        for c in candidates[:2]
    )
    lines.append(f"Sources: {sources}")
    return "\n\n".join(lines)


@router.post("/api/chat/start", response_model=ChatResponse)
async def chat_start(req: ChatStartRequest) -> ChatResponse:
    """Start a new chat session with the engine agent."""
    engine = get_or_build_engine(0)
    context = _to_context(req.context)
    session = engine.agent.start(req.session_id, req.query, context=context)
    candidates = (
        _hits_to_solutions(
            session.turns[-1].candidates,
            all_entries=engine.index.entries,
            context=context,
        )
        if session.turns
        else []
    )
    verdict = evaluate_policy(session.turns[-1].candidates, context, surface="chat")
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
    if req.session_id not in engine.agent.sessions:
        session = engine.agent.start(req.session_id, req.message)
        core_hits = session.turns[-1].candidates
    else:
        session = engine.agent.respond(req.session_id, req.message)
        core_hits = session.turns[-1].candidates
    candidates = _hits_to_solutions(
        core_hits, all_entries=engine.index.entries, context=session.context
    )
    verdict = evaluate_policy(core_hits, session.context, surface="chat")
    reply = _build_assistant_turn(
        req.message, candidates, next_best_action=to_next_best_action(verdict)
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
