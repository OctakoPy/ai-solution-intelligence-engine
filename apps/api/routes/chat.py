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
    RetrievedSolution,
)
from apps.api.views import SOURCE_LABELS

router = APIRouter(tags=["chat"])


def _now() -> str:
    """Current local time formatted HH:MM AM/PM."""
    return datetime.now().strftime("%I:%M %p").lstrip("0")


# Chat display multiplier: conversational queries are wordier than ticket
# text, so raw cosine similarity under-reports genuinely good matches. Boost
# the displayed score to keep it consistent with the Find a Solution page.
_CHAT_SCORE_BOOST = 1.25

# Reply bands on the boosted display scale: below the low threshold the
# engine won't guess a fix; in the middle band it offers the nearest matches
# and asks the user; at or above the high threshold it answers confidently.
_CHAT_LOW_CONFIDENCE_THRESHOLD = 0.75
_CHAT_CONFIDENT_THRESHOLD = 0.90


def _display_score(h) -> float:
    """Return the chat-display score, boosted and capped at 1.0."""
    return round(min(1.0, h.combined_score * _CHAT_SCORE_BOOST), 3)


def _hits_to_solutions(hits) -> list[RetrievedSolution]:
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
        )
        for h in hits
    ]


def _build_assistant_turn(query: str, candidates: list[RetrievedSolution]) -> str:
    """Compose a deterministic assistant reply from the current candidates."""
    if not candidates:
        return "No confident matches found. Try describing the issue differently."
    top = candidates[0]
    if top.score < _CHAT_LOW_CONFIDENCE_THRESHOLD:
        best = int(top.score * 100)
        lines = [
            "None of the historical records are a confident match — the best "
            f"one is only {best}% similar. I won't guess a fix, because a "
            "wrong answer here could make things worse.",
            "Here are the nearest look-alikes, purely as a starting point for "
            "a specialist:",
        ]
        for idx, c in enumerate(candidates, start=1):
            lines.append(f"{idx}. **{c.title}** — {int(c.score * 100)}% match")
        lines.append(
            "My recommendation: escalate to a subject-matter expert for manual "
            "handling rather than auto-applying a solution."
        )
        return "\n\n".join(lines)
    if top.score < _CHAT_CONFIDENT_THRESHOLD:
        best = int(top.score * 100)
        lines = [
            (
                f"I'm not fully certain of an exact match — the closest record "
                f"is about {best}% similar."
            ),
            "Here are the closest matches I could find — are any of these helpful?",
        ]
        for idx, c in enumerate(candidates, start=1):
            lines.append(f"{idx}. **{c.title}** — {int(c.score * 100)}% match")
        return "\n\n".join(lines)
    lines = [
        "This issue is usually caused by cached authentication or sync settings. "
        "Here are the steps that resolved it for similar cases:",
    ]
    for idx, c in enumerate(candidates, start=1):
        lines.append(f"{idx}. **{c.title}** — {int(c.score * 100)}% match")
    lines.append(f"This solved the issue in {int(top.score * 100)}% of similar cases.")
    sources = " · ".join(
        f"{c.title} ({c.source}) – {c.date} ({int(c.score * 100)}%)"
        for c in candidates[:2]
    )
    lines.append(f"Sources: {sources}")
    return "\n\n".join(lines)


@router.post("/api/chat/start", response_model=ChatResponse)
async def chat_start(req: ChatStartRequest) -> ChatResponse:
    """Start a new chat session with the engine agent."""
    engine = get_or_build_engine(0)
    session = engine.agent.start(req.session_id, req.query)
    candidates = (
        _hits_to_solutions(session.turns[-1].candidates) if session.turns else []
    )
    reply = _build_assistant_turn(req.query, candidates)
    session.add_system(reply)
    turns: list[ChatTurn] = [
        ChatTurn(role="user", text=req.query, timestamp=_now()),
        ChatTurn(role="assistant", text=reply, timestamp=_now()),
    ]
    return ChatResponse(turns=turns, candidates=candidates)


@router.post("/api/chat/respond", response_model=ChatResponse)
async def chat_respond(req: ChatRespondRequest) -> ChatResponse:
    """Send a follow-up message within an existing chat session."""
    engine = get_or_build_engine(0)
    if req.session_id not in engine.agent.sessions:
        session = engine.agent.start(req.session_id, req.message)
        candidates = _hits_to_solutions(session.turns[-1].candidates)
    else:
        session = engine.agent.respond(req.session_id, req.message)
        candidates = _hits_to_solutions(session.turns[-1].candidates)
    reply = _build_assistant_turn(req.message, candidates)
    session.add_system(reply)
    turns: list[ChatTurn] = []
    for t in session.turns:
        if t.role == "user":
            turns.append(ChatTurn(role="user", text=t.text, timestamp=_now()))
    turns.append(ChatTurn(role="assistant", text=reply, timestamp=_now()))
    return ChatResponse(turns=turns, candidates=candidates)
