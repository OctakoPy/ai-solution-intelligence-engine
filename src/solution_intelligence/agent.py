"""Conversational refinement agent for the chat demo.

Instead of calling an external model, the demo agent applies deterministic
intent detection to follow-up messages and re-scores the candidate list so a
non-technical audience can watch the conversation steer the retrieval.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from solution_intelligence.models import RetrievedSolution
from solution_intelligence.policy import prefer_topical
from solution_intelligence.retrieval import (
    ConfidenceScorer,
    IncidentContext,
    KnowledgeIndex,
    rank_results,
)


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
    context: IncidentContext | None = None
    turns: list[ChatTurn] = field(default_factory=list)
    # Entry ids the user has told us did not work in *this* conversation.
    # This is conversation-scoped, unlike the global worked_count feedback:
    # it answers "this fix did not help here", not "this fix is bad".
    rejected: set[str] = field(default_factory=set)
    # Titles of rejected records, newest last, so the reply can name what
    # it ruled out after the record has already been demoted out of the
    # candidate list.
    rejected_titles: list[str] = field(default_factory=list)

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

    def __init__(
        self,
        index: KnowledgeIndex,
        scorer: ConfidenceScorer | None = None,
    ) -> None:
        self.index = index
        self.scorer = scorer or ConfidenceScorer()
        self.sessions: dict[str, ChatSession] = {}

    def start(
        self,
        session_id: str,
        query: str,
        context: IncidentContext | None = None,
    ) -> ChatSession:
        """Create a session and return the initial candidate list.

        Uses the same shared outcome-aware ranking path as Find a Solution,
        so identical query + context rank identically on both surfaces, and
        promotes a record that is actually about the question's subject. The
        session stores the order the user is shown, which is what a later
        "that did not work" has to refer back to.
        """
        candidates = rank_results(
            index=self.index,
            query=query,
            top_k=5,
            context=context,
        )
        candidates = prefer_topical(candidates, query, context)
        session = ChatSession(query=query, context=context)
        session.add_user(query, candidates)
        self.sessions[session_id] = session
        return session

    def respond(
        self,
        session_id: str,
        message: str,
        top_k: int = 5,
        context: IncidentContext | None = None,
    ) -> ChatSession:
        """Process a follow-up message and update the session.

        A follow-up can do three things, in this order:

        * supply structured detail (error code / module / environment), which
          is merged into the session context so it informs every later
          re-rank instead of being forgotten after one turn;
        * report that the recommended fix failed, which rules that record
          out *for this conversation* and demotes it below the remaining
          candidates;
        * otherwise refine the query, broadening or excluding terms.
        """
        session = self.sessions.get(session_id)
        if session is None:
            return self.start(session_id, message, context)

        # 1. Keep any structured detail the user just gave us.
        supplied = extract_context(message)
        if supplied:
            session.context = merge_context(session.context, supplied)

        # 2. A rejection rules out the record we recommended last turn.
        if _REJECTION.search(message):
            for turn in reversed(session.turns):
                if turn.candidates:
                    top_candidate = turn.candidates[0]
                    if top_candidate.entry.id not in session.rejected:
                        session.rejected.add(top_candidate.entry.id)
                        session.rejected_titles.append(top_candidate.entry.title)
                    break

        intent = detect_intent(message)
        boost_terms = _extract_boost_terms(message)

        effective_query = (
            f"{session.query} {message}"
            if intent in ("broaden", "more")
            else session.query
        )
        candidates = rank_results(
            index=self.index,
            query=effective_query,
            top_k=top_k,
            context=session.context,
            adjust=lambda c: _apply_adjustments(c, boost_terms, session.rejected),
        )
        candidates = prefer_topical(
            candidates, f"{session.query} {message}", session.context
        )

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


# Environments and modules are named in free text during a conversation, so
# the follow-up handler recognises them and keeps them for later re-ranking.
_ENVS = ("prod", "production", "qa", "quality", "dev", "development", "test")

_MODULES = (
    "sap fico",
    "sap mm",
    "sap co",
    "sap hcm",
    "sap basis",
    "sap fiori",
    "sap workflow",
    "sap interfaces",
    "active directory",
    "exchange online",
    "sharepoint",
    "end user hardware",
    "microsoft licensing",
    "hr onboarding",
    "vpn",
)

# An SAP-style error code: letter(s), underscore, letter(s), e.g. S_RS_COMP.
_ERROR_CODE = re.compile(r"\b([A-Z]{1,3}[_/][A-Z0-9]{2,12})\b")

# Wording that means "the thing you just recommended did not work". These are
# negative outcomes for this conversation only; they must not be confused
# with the global success feedback, which judges the fix itself.
_REJECTION = re.compile(
    r"\b(did(?:n't| not)|does(?:n't| not)|do(?:n't| not)|no (?:it|that) (?:did|didn)"
    r"|still (?:not|isn'?t|doesn'?t|failing|broken|error)|not work(?:ed|ing)?|"
    r"no luck|didn'?t help|already tried|that failed|failed again|"
    r"same (?:error|issue|problem)|not fixed|still the same)\b",
    re.IGNORECASE,
)

# Wording that means the recommended fix worked.
_SUCCESS = re.compile(
    r"\b(that (?:worked|fixed it|did it)|works now|fixed it|resolved|"
    r"all good|back to normal|working now)\b",
    re.IGNORECASE,
)


def extract_context(message: str) -> dict[str, str]:
    """Pull structured incident fields out of a conversational follow-up.

    Returns only the fields the user actually supplied, so the caller can
    merge them into the session context without inventing values.
    """
    found: dict[str, str] = {}
    lowered = message.lower()

    code_match = _ERROR_CODE.search(message)
    if code_match:
        found["error_code"] = code_match.group(1)
    else:
        # "error code is X" / "code X" without underscores still counts.
        words = re.findall(r"\b[A-Z]{2,}\b", message)
        if words:
            found["error_code"] = words[0]

    for env in _ENVS:
        if re.search(rf"\b{env}\b", lowered):
            found["environment"] = env.upper() if env in ("prod", "qa") else env
            break

    for module in _MODULES:
        if module in lowered:
            found["module"] = " ".join(w.capitalize() for w in module.split())
            break

    return found


def merge_context(
    existing: IncidentContext | None,
    supplied: dict[str, str],
) -> IncidentContext | None:
    """Merge newly supplied context fields into what the session already has.

    Values the user has given earlier are kept: a follow-up that mentions
    only the error code must not erase the module and environment supplied
    in the message before it.
    """
    if not supplied:
        return existing
    return IncidentContext(
        error_code=supplied.get("error_code")
        or (existing.error_code if existing else None),
        module=supplied.get("module") or (existing.module if existing else None),
        environment=supplied.get("environment")
        or (existing.environment if existing else None),
    )


def _apply_boosts(
    candidate: RetrievedSolution,
    terms: list[str],
) -> None:
    """Nudge a candidate's raw similarity up for each refinement-term match.

    Runs inside the shared ranking path's ``adjust`` hook, before the
    outcome-aware confidence is recomputed, so conversational refinements
    shift the same ranking scale instead of introducing a second one.
    """
    haystack = f"{candidate.entry.title} {candidate.entry.description}".lower()
    matches = sum(1 for t in terms if t in haystack)
    candidate.score = round(min(1.0, candidate.score + 0.05 * matches), 3)


def _apply_adjustments(
    candidate: RetrievedSolution,
    terms: list[str],
    rejected: set[str],
) -> None:
    """Apply conversational boosts, then demote anything already ruled out.

    A record the user has reported as failing in this conversation loses its
    claim to be the answer: its raw similarity is cut hard so it sorts below
    every un-rejected candidate. It is not removed, so if it genuinely is the
    only related record it still surfaces last and the abstain policy decides
    whether that is enough to recommend it.
    """
    if candidate.entry.id in rejected:
        candidate.score = round(candidate.score * 0.1, 3)
        return
    _apply_boosts(candidate, terms)
