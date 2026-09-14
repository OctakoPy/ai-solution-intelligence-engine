"""Conversational refinement agent for the chat demo.

Instead of calling an external model, the demo agent applies deterministic
intent detection to follow-up messages and re-scores the candidate list so a
non-technical audience can watch the conversation steer the retrieval.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from solution_intelligence.models import RetrievedSolution
from solution_intelligence.retrieval import KnowledgeIndex


@dataclass
class ChatTurn:
    """One message in the conversational demo."""

    role: str  # user | system
    text: str
    candidates: list[RetrievedSolution] = field(default_factory=list)


@dataclass
class ChatSession:
    """State of a single chat conversation."""

    query: str = ""
    turns: list[ChatTurn] = field(default_factory=list)

    def add_user(self, text: str, candidates: list[RetrievedSolution]) -> None:
        self.turns.append(ChatTurn(role="user", text=text, candidates=candidates))

    def add_system(self, text: str) -> None:
        self.turns.append(ChatTurn(role="system", text=text))


_REFINE_PATTERNS = [
    (re.compile(r"\b(also|and|plus|as well)\b", re.IGNORECASE), "broaden"),
    (re.compile(r"\b(more|another|other)\b", re.IGNORECASE), "more"),
    (re.compile(r"\b(not|without|minus|exclude|remove)\b", re.IGNORECASE), "exclude"),
    (
        re.compile(
            r"\b(specifically|exactly|windows|linux|sap|fiori|fi|batch)\b",
            re.IGNORECASE,
        ),
        "specific",
    ),
]


def detect_intent(message: str) -> str:
    """Classify a follow-up message into an intent bucket."""
    lower = message.lower()
    for pattern, intent in _REFINE_PATTERNS:
        if pattern.search(lower):
            return intent
    return "unknown"


class ConversationalAgent:
    """Handles a chat session and refines retrieval on new messages."""

    def __init__(self, index: KnowledgeIndex) -> None:
        self.index = index
        self.sessions: dict[str, ChatSession] = {}

    def start(self, session_id: str, query: str) -> ChatSession:
        """Create a session and return the initial candidate list."""
        candidates = self.index.query(query, top_k=5)
        session = ChatSession(query=query)
        session.add_user(query, candidates)
        self.sessions[session_id] = session
        return session

    def respond(
        self,
        session_id: str,
        message: str,
        top_k: int = 5,
    ) -> ChatSession:
        """Process a follow-up message and update the session.

        Uses a simple keyword-based re-ranking: messages that surface a
        specific keyword are used to boost matching candidates.
        """
        session = self.sessions.get(session_id)
        if session is None:
            session = self.start(session_id, message)
            return session

        intent = detect_intent(message)
        boost_terms = _extract_boost_terms(message)

        if intent in ("broaden", "more"):
            candidates = self.index.query(f"{session.query} {message}", top_k=top_k)
        else:
            candidates = self.index.query(session.query, top_k=top_k)

        if boost_terms:
            candidates = _apply_boosts(candidates, boost_terms)

        session.add_user(message, candidates)
        return session


def _extract_boost_terms(message: str) -> list[str]:
    """Pull meaningful single words from a message to use as boosts."""
    stop = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "for",
        "with",
        "also",
        "as",
        "well",
        "another",
        "other",
        "more",
        "not",
        "please",
        "also",
    }
    words = re.findall(r"[A-Za-z]{4,}", message.lower())
    return [w for w in words if w not in stop][:4]


def _apply_boosts(
    candidates: list[RetrievedSolution],
    terms: list[str],
) -> list[RetrievedSolution]:
    """Re-rank candidates that match refinement terms higher."""
    for candidate in candidates:
        haystack = f"{candidate.entry.title} {candidate.entry.description}".lower()
        matches = sum(1 for t in terms if t in haystack)
        candidate.score = round(min(1.0, candidate.score + 0.05 * matches), 3)
    candidates.sort(key=lambda c: c.combined_score, reverse=True)
    return candidates
