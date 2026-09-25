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

import re
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
# the record's history is strong — the score says the query is not
# really about this record, so the banner still appears.
PROVEN_FLOOR = 0.35
# A record that has worked every time (with enough attempts) is a go
# regardless of composite confidence. Abstain is for genuinely
# weak / unproven matches.
PROVEN_MIN_ATTEMPTS = 3
# A record that is not flawless can still be trusted, but only on a real
# sample and only at a high rate. Requiring perfection (worked == attempted)
# discarded fixes that worked 15 times out of 17 as unproven, which made
# Find a Solution escalate on records whose own history says they usually
# work. This is a trust bar for the abstain decision only: the Overview
# "proven fixes" counter still means flawless, and the two must not be
# conflated.
TRUSTED_MIN_ATTEMPTS = 5
TRUSTED_MIN_SUCCESS_RATE = 0.80

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


def is_trusted(top: RetrievedSolution | None) -> bool:
    """True when a record's own history is strong enough to act on.

    The abstain policy asks "would a consultant apply this fix?", which is
    not the same question as "has this fix never failed once". Requiring
    perfection for the first question threw away fixes with long, mostly
    positive histories: Outlook sync at 15 of 17, SharePoint access at 16 of
    18, a VPN fix at 11 of 13. Those are the records an admin most wants
    surfaced, because their own outcome data says they usually work.

    A small sample is not enough to be called trustworthy, so this needs
    both a floor on attempts and a high success rate. It is deliberately
    separate from :func:`is_proven`, which keeps its stricter meaning for
    the Overview "proven fixes" counter and for anything that claims a fix
    has never failed.
    """
    if top is None or top.entry is None:
        return False
    attempted = top.entry.attempted
    if attempted < TRUSTED_MIN_ATTEMPTS:
        return False
    return (top.entry.worked / attempted) >= TRUSTED_MIN_SUCCESS_RATE


# Vocabulary for recognising which *subject* a query and a record talk
# about. The point of the topical gate is to require independent evidence
# that the record is about the user's problem before a good track record
# is allowed to vouch for a weak composite score.
#
# A bare vendor name is deliberately not enough on its own: "SAP" appears
# in every SAP record, so treating it as a match would let any SAP record
# answer any SAP question. The bare vendor is therefore kept in a separate
# set - it can confirm that two texts are in the same estate, but a match
# also needs a specific subject below.
_VENDORS: dict[str, tuple[str, ...]] = {
    "sap": ("sap", "sapo", "abap", "fiori", "launchpad", "su01", "su53", "idoc"),
    "microsoft": (
        "outlook",
        "exchange",
        "sharepoint",
        "teams",
        "onedrive",
        "active directory",
    ),
    "cisco": ("vpn", "anyconnect", "fortinet"),
    "windows": ("windows", "intune", "endpoint"),
    "apple": ("macbook", "iphone", "ipad"),
}

# Categories are already assigned per record by ingestion, and they separate
# SAP authorization from SAP performance far more reliably than keyword
# matching on prose can: a description about authorization often mentions a
# purchase order in passing, which made an authorization record look like an
# SAP MM record. The record's own category is therefore authoritative, and
# the subject vocabulary below is used only for the *query* side, which has
# no category.
_SUBJECT_OF_CATEGORY: dict[str, str] = {
    "sap_authorization": "sap_authorization",
    "sap_batch_jobs": "sap_batch",
    "sap_fiori": "sap_fiori",
    "sap_interfaces": "sap_interfaces",
    "sap_materials": "sap_mm",
    "sap_workflow": "sap_workflow",
    "sap_addons": "sap_addons",
    "account_access": "ad_account",
    "email": "outlook_mail",
    "hardware": "hardware",
    "hr_systems": "hr_systems",
    "kb_maintenance": "kb_maintenance",
    "licensing": "licensing",
    "network_vpn": "vpn",
    "onboarding": "onboarding",
    "compliance": "compliance",
    "sharepoint_access": "sharepoint_access",
}

# The vendor names themselves. A module whose only meaningful term is one of
# these describes the whole estate, not a system, so it cannot vouch for a
# record on its own.
_VENDOR_NAMES: frozenset[str] = frozenset(
    {"sap", "sapo", "microsoft", "windows", "cisco", "apple"}
)

# Module names that name a vendor rather than a specific system. They cannot
# vouch for a record on their own, so the topical gate ignores them.
_VENDOR_ONLY_MODULES: frozenset[str] = frozenset(
    vendor for vendor in ("sap", "sap ", "microsoft", "windows")
)

# Module names, used to work out which subject a record belongs to when it
# has no category (and to confirm the record is even in the same system).
_SUBJECT_OF_MODULE: dict[str, str] = {
    "sap fico": "sap_authorization",
    "sap co": "sap_authorization",
    "sap basis": "sap_authorization",
    "sap mm": "sap_mm",
    "sap fiori": "sap_fiori",
    "sap workflow": "sap_workflow",
    "sap interfaces": "sap_interfaces",
    "sap": "sap_gui_performance",
    "vpn": "vpn",
    "active directory": "ad_account",
    "exchange online": "outlook_mail",
    "sharepoint": "sharepoint_access",
    "microsoft licensing": "licensing",
    "hr onboarding": "onboarding",
    "hr systems": "hr_systems",
    "compliance": "compliance",
    "knowledge base": "kb_maintenance",
    "end user hardware": "printer",
}

# Specific subjects a *query* can name. A match on one of these is real
# topical evidence. "FI report" and "authorization" are the same subject:
# a user reporting they cannot run an FI report is describing a role
# problem, which is how these records are actually filed.
_SUBJECTS: dict[str, tuple[str, ...]] = {
    "sap_authorization": (
        "su01",
        "su53",
        "s_rcomp",
        "s_rs_comp",
        "authorization",
        "authorisation",
        "role assignment",
        "fbl3n",
        "fbl1n",
        "access rights",
        "not authorized",
        "not authorised",
        "permission error",
        "fi report",
        "financial report",
        "report access",
        "sap fi",
        "reporting",
        # Plain English: what a non-technical user actually types.
        "will not open",
        "won't open",
        "cannot open",
        "can't open",
        "not authorized",
        "access denied",
        "permission denied",
        "no permission",
        "am i allowed",
    ),
    "sap_mm": (
        "me23n",
        "me21n",
        "m8149",
        "goods receipt",
        "purchase order",
        "inbound delivery",
        "posting error",
        "account determination",
        # Plain English.
        "order failed",
        "delivery failed",
        "stock",
        "delivery",
    ),
    "sap_fiori": ("fiori", "launchpad", "launch pad", "tile", "approve request"),
    "sap_workflow": (
        "workflow",
        "attachment",
        "inbox item",
        # Plain English.
        "spreadsheet",
        "excel file",
        "sent to me",
        "open a file",
    ),
    "sap_batch": (
        "batch job",
        "short dump",
        "st22",
        "scheduled job",
        "scheduler",
        "nightly job",
    ),
    "sap_gui_performance": (
        "sap gui",
        "saplogon",
        "gui login",
        "logon slow",
        "logging in to sap is slow",
        "sap login is slow",
    ),
    "sap_interfaces": (
        "idoc",
        "rfc",
        "interface",
        "integration",
        "logistics",
        "edi",
        "message log",
    ),
    "sap_addons": (
        "add-on",
        "addon",
        "session timeout",
        "time out",
        "timing out",
        "enhancement",
        "plug-in",
    ),
    "hr_systems": (
        "hr system",
        "personnel",
        "personal data",
        "employee record",
        "payroll",
        "hris",
        "badgedata",
    ),
    "compliance": (
        "audit",
        "compliance",
        "historical tickets",
        "export tickets",
        "regulator",
        "retention",
    ),
    "hardware": (
        "printer",
        "print",
        "toner",
        "paper jam",
        "spooler",
        "laptop",
        "monitor",
        "display",
        "docking station",
        "battery",
    ),
    "kb_maintenance": (
        "kb article",
        "knowledge base",
        "outdated article",
        "outdated kb",
        "documentation is wrong",
    ),
    "sap_basis": ("sap basis", "transport", "client copy", "stms"),
    "vpn": (
        "vpn",
        "tunnel",
        "remote access",
        "disconnect",
        "anyconnect",
        "disconnecting",
        # Plain English.
        "keeps dropping",
        "drops every",
        "working from home",
        "remote worker",
    ),
    "outlook_mail": (
        "mail",
        "email",
        "inbox",
        "smtp",
        "autoforward",
        "calendar",
        "signature",
        "sending",
        "cannot send",
        # Plain English.
        "not arriving",
        "not receiving",
        "no email",
        "missing email",
        "stuck in outbox",
    ),
    "outlook_sync": (
        "sync",
        "ost",
        "ostf",
        "cached mode",
        "global catalog",
        "not syncing",
    ),
    "outlook_delivery": ("delayed", "queue", "delivery", "hours late"),
    "ad_account": (
        "locked out",
        "account lock",
        "password reset",
        "failed login",
        "unlock",
        "forgot password",
        # Plain English.
        "forgot my password",
        "forgot the password",
        "cannot log in",
        "can't log in",
        "cannot sign in",
        "can't sign in",
        "locked out of my",
        "password does not work",
        "password doesn't work",
    ),
    "ad_group": ("group policy", "gpo", "permissions", "delegation"),
    "sharepoint_access": (
        "sharepoint",
        "site access",
        "document library",
        "permission",
        "inheritance",
        "cannot access",
        # Plain English.
        "website i need",
        "site i need",
        "cannot get into",
        "can't get into",
        "shared drive",
        "team site",
    ),
    "printer": ("printer", "print", "toner", "paper jam", "spooler"),
    "laptop_hardware": ("laptop", "won't turn on", "battery", "no power", "boot"),
    "monitor": ("monitor", "flicker", "display", "screen", "vga"),
    "licensing": ("license", "licence", "seat", "activation", "subscription"),
    "onboarding": (
        "onboard",
        "new hire",
        "new employee",
        "new starter",
        "laptop setup",
    ),
}


def _tokens(text: str) -> set[str]:
    """Lowercase word tokens of a text, for domain-vocabulary matching."""
    return set(re.findall(r"[a-z0-9_]+", text.lower()))


def _matches(text: str, table: dict[str, tuple[str, ...]]) -> set[str]:
    """Which named subjects or vendors a piece of text refers to."""
    lowered = text.lower()
    found: set[str] = set()
    for name, words in table.items():
        for word in words:
            if " " in word:
                if word in lowered:
                    found.add(name)
                    break
            elif word in _tokens(lowered):
                found.add(name)
                break
    return found


def _record_subject(entry: KnowledgeEntry) -> str | None:
    """The single subject a record belongs to, from its own metadata.

    The category wins when present because ingestion assigned it to the
    record as a whole; the module is the fallback for records that have no
    category. Returns ``None`` when the record says nothing about itself, in
    which case the caller falls back to matching its prose.
    """
    subject = _SUBJECT_OF_CATEGORY.get((entry.category or "").strip().lower())
    if subject:
        return subject
    return _SUBJECT_OF_MODULE.get((entry.module or "").strip().lower())


def _is_topical(
    query: str,
    top: RetrievedSolution | None,
    context: IncidentContext | None,
) -> bool:
    """True when there is evidence beyond the composite score that this
    record is about the user's problem.

    The composite confidence already rewards a strong success history
    (weight 0.20 in the outcome-aware score). Letting that same history
    also *veto* the abstain decision re-applies one piece of evidence
    twice, so a popular but unrelated record gets presented as a certain
    answer. This gate instead requires independent topical evidence.

    Evidence is checked strongest-first:

    1. an exact structured-field agreement (error code, module, environment);
    2. the record's ``module`` named in the query or in supplied context;
    3. the query naming the same *subject* the record is filed under, within
       the same system.

    Sharing only a vendor is not evidence: every SAP record says "SAP", so
    that would let a batch-job record answer an authorization question and
    the reverse.
    """
    if top is None or top.entry is None:
        return False
    entry = top.entry

    query_text = " ".join(
        part
        for part in (
            query,
            context.module if context else None,
            context.error_code if context else None,
            context.environment if context else None,
        )
        if part
    ).lower()

    # 1. Exact agreement on a structured field is the strongest evidence.
    if context is not None:
        for query_value, entry_value in (
            (context.error_code, entry.error_code),
            (context.module, entry.module),
            (context.environment, entry.environment),
        ):
            if not query_value or not entry_value:
                continue
            if query_value.strip().lower() == entry_value.strip().lower():
                return True

    if not query_text.strip():
        return False

    # 2. The record's module named in the query, or in supplied context.
    #    A module made only of the vendor ("SAP", "SAP CO") names nothing
    #    specific, so matching it would accept every query in that estate:
    #    "SAP CO" is satisfied by a bare "SAP" in the query. Those records
    #    carry no evidence of their own and fall through to the subject
    #    check, which is what actually tells the systems apart.
    if entry.module and entry.module.strip().lower() not in _VENDOR_ONLY_MODULES:
        module = entry.module.strip().lower()
        if module in query_text:
            return True
        # Every part of the module name has to appear, and at least one of
        # them has to be specific to a system rather than the vendor.
        module_terms = {t for t in re.findall(r"[a-z0-9]+", module) if len(t) > 2}
        specific = {t for t in module_terms if t not in _VENDOR_NAMES}
        if specific and module_terms <= _tokens(query_text):
            return True

    # 3. Same subject. The vendor is only a tie-breaker against a wrong
    #    estate: a query that names none ("printer on 3th floor") must still
    #    be able to match a printer record, so disagreement is what matters,
    #    not presence. Subjects are specific enough to carry the match on
    #    their own.
    record_text = " ".join(part for part in (entry.title, entry.description) if part)
    query_vendors = _matches(query_text, _VENDORS)
    record_vendors = _matches(record_text, _VENDORS)
    if query_vendors and record_vendors and not (query_vendors & record_vendors):
        return False

    query_subjects = _matches(query_text, _SUBJECTS)
    subject = _record_subject(entry)

    if not query_subjects:
        # The query names no specific subject. "The custom abap program
        # zreport99 keeps erroring" is still answerable: the user said which
        # estate they are in, and the semantic score picks the record. A
        # query that names no system at all ("i ran out of milk") says
        # nothing, and must not be handed a record just because it lacks
        # evidence against one.
        return bool(query_vendors and record_vendors and query_vendors & record_vendors)

    if subject is not None:
        if subject in query_subjects:
            return True
        # Some categories are deliberately coarse - every Outlook record is
        # filed as "email", whether it is about syncing, sending or
        # calendars. When the category and the query name different subjects
        # inside the same system, the record's own text decides, so "not
        # syncing" still reaches the sync record.
        if query_vendors and record_vendors and (query_vendors & record_vendors):
            return bool(query_subjects & _matches(record_text, _SUBJECTS))
        return False

    # The record has no usable metadata, so fall back to its prose.
    return bool(query_subjects & _matches(record_text, _SUBJECTS))


def is_topical(
    query: str,
    top: RetrievedSolution | None,
    context: IncidentContext | None,
) -> bool:
    """True when a record is about the subject the user actually asked about.

    Exposed so ranking can prefer a topical record over a better-scoring
    one from the wrong subject, rather than only overrule it afterwards.
    """
    return _is_topical(query, top, context)


def prefer_topical(
    hits: list[RetrievedSolution],
    query: str,
    context: IncidentContext | None,
) -> list[RetrievedSolution]:
    """Reorder hits so a record about the query's subject leads the list.

    Retrieval ranks on similarity, which on a shallow index can put a
    well-trodden but wrong-subject record first ("both mention SAP"). The
    abstain policy then has to overrule it, and the banner and the card
    disagree. Promoting the topical record here keeps one ranking for the
    policy, the reply, and the cards the user reads.

    It lives in the core policy rather than the API because the chat session
    has to remember the order it *presented*: a later "that did not work"
    has to rule out the record the user actually saw, which is not always
    the raw top hit. Among records that are all topical the existing order
    is kept, so this only ever promotes on subject.
    """
    if not hits:
        return hits
    if is_topical(query, hits[0], context):
        return hits
    for index, candidate in enumerate(hits[1:], start=1):
        if is_topical(query, candidate, context):
            return [candidate, *hits[:index], *hits[index + 1 :]]
    return hits


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
    query: str = "",
    context: IncidentContext | None = None,
    abstain_threshold: float = ABSTAIN_THRESHOLD,
    confident_threshold: float = CONFIDENT_THRESHOLD,
    candidates: list[RetrievedSolution] | None = None,
) -> PolicyVerdict:
    """Apply the shared abstain policy to a retrieval result.

    Args:
        top: The highest-ranked candidate (``None`` when nothing matched).
        query: The user's own words, used only by the topical gate below.
        context: Optional structured incident context; used to ask for the
            specific missing fields rather than generic "more detail".
        abstain_threshold: Below this confidence the engine escalates.
        confident_threshold: At or above this the engine proceeds.
        candidates: The other ranked candidates, used to fall back to a
            topical record when the top hit is not about this query.

    Returns:
        A :class:`PolicyVerdict` whose payload is deterministic for a given
        result, so the same query always produces the same guidance.
    """
    confidence = top.confidence if top is not None else 0.0

    # A record the query has no subject in common with must not be answered
    # just because it scored well or has a perfect history. Both of those
    # say "this fix works when it applies", never "this fix applies here".
    # When a topical candidate does exist, the engine uses that one instead
    # of declining outright: a mismatched top hit is a ranking problem, and
    # the topical candidate is a better answer.
    if top is not None and not _is_topical(query, top, context):
        topical = next(
            (
                candidate
                for candidate in (candidates or [])
                if _is_topical(query, candidate, context)
            ),
            None,
        )
        if topical is not None and topical is not top:
            top = topical
            confidence = topical.confidence

    if confidence >= confident_threshold:
        return PolicyVerdict(action="proceed")
    if confidence >= abstain_threshold:
        return PolicyVerdict(
            action="ask_context",
            next_best_action=_ask_context_payload(top, context),
        )
    if (
        is_trusted(top)
        and confidence >= PROVEN_FLOOR
        and _is_topical(query, top, context)
    ):
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
    """Build the escalate-to-SME next-best-action payload.

    The message names no percentage. The composite score is a weighted blend,
    not a probability, so a figure like "51%" reads to a business audience as
    "a 51% chance this is right" while the sentence around it says the engine
    will not answer. Stating the reason in words is both plainer and more
    honest. The numeric score stays available on the record itself for anyone
    who wants to see it.
    """
    nearest: dict[str, str] | None = None
    if top is not None and top.entry is not None:
        nearest = {"id": top.entry.id, "title": top.entry.title}
        message = (
            "Nothing in the knowledge base matches this closely enough to "
            "recommend. Escalate to a subject-matter expert rather than "
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
