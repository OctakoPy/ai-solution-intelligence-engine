# ResolveIQ — Project Details (combined deck)

> For the teammate building the slide deck. Every benefit from the original
> proposal **and** the latest ResolveIQ demo deck is merged here. Each item is
> written for a business audience — what it does, and why it matters — so it can
> go straight onto a slide.

---

## One line

**ResolveIQ turns your team's messy history of "we already solved this" into an
assistant that finds the best-known fix instantly — and honestly tells you when
it doesn't have one.**

---

## The problem (why it matters)

Enterprise IT consultants handle **hundreds of incidents a day**. Most are
variations of problems the team already solved — but the knowledge is scattered
across **tickets, SAP repositories, SharePoint, and knowledge bases**, with
**no way to search them all at once**. So consultants:

- hunt system-by-system to find a past fix,
- re-solve recurring issues **from scratch**, and
- recreate fixes that already exist elsewhere.

There's also **no feedback loop**: even when a good fix is found, nothing tracks
whether it actually worked, so knowledge quality never improves on its own.

The result: **duplicated effort, inconsistent solutions, and longer resolution
times** — all avoidable. The fix is usually out there. It's just not findable
*at the moment it's needed*.

---

## The engine (what it is)

ResolveIQ is **not a search box with an LLM attached**. It's a **resolution
decision layer**: it understands the incident, retrieves the closest historical
fixes across all four sources at once, **ranks them by what actually worked**,
and explains every recommendation. When it can't be confident, **it says so**
instead of inventing an answer.

A consultant inputs clear context (error code, module, environment) and gets
back ranked candidate fixes — each with a **similarity %, prior success rate,
source, and reasoning**. To refine, they can steer in plain language: *"also
check cases involving a VPN timeout"*.

---

## The benefits (all of them, from both versions)

### 1. Instant cross-system search

One plain-language query returns ranked matches from **tickets + SAP +
SharePoint + knowledge bases simultaneously**. No more searching system by
system.

**Business benefit:** the #1 reason support is slow — hunting for the fix —
drops from minutes of manual searching to an instant answer.

### 2. Proven fixes win — not just similar ones

Solutions are ranked by their **historical track record**, not only similarity.
A fix that "worked **8 of 8** times" ranks above a merely
similar-sounding one.

**Business benefit:** the *effective* answer surfaces, not the most
similar-sounding one. You trust it because it worked before.

### 3. Knows when NOT to guess (honesty)

When no historical record is a confident match, ResolveIQ **changes its
action**: it shows an amber banner — "I don't have a confident answer for this
one" — and hands off to a subject-matter expert **instead of applying a guess**.

**Business benefit:** in enterprise IT, a wrong answer carries real cost.
ResolveIQ is honest about uncertainty, so consultants never get a confident
fix for something the engine genuinely doesn't know.

### 4. Full transparency — the "Why Panel"

Every result shows **where it came from, its similarity %, its prior success
rate ("worked 8 of 8"), and the reasoning** behind the score. No black box.

**Business benefit:** trust and auditability. Every recommendation is traceable
and verifiable — consultants know *why* a fix was recommended, not just that it
was.

### 5. Predictive confidence scoring

The confidence score is a **prediction of how likely this fix is to work for
this specific case**, based on real historical outcomes — not a blind
similarity %.

**Business benefit:** the engine tells you how confident it is, so the team
knows how much to trust each answer.

### 6. Understands context, not just keywords

ResolveIQ uses the incident's **error code, module, and environment** — and
knows when that context conflicts (a **context trap**: same error code,
different root cause). It surfaces "why this may not apply here."

**Business benefit:** avoids the classic support pitfall — matching the right
error code but the wrong root cause.

### 7. Human-in-the-loop autonomy

The engine **recommends and explains**; a human (consultant) **decides**.
Proven, low-risk fixes (e.g. password reset) can be auto-applied; anything
uncertain goes to a human for approve / reject / choose-an-alternative.

**Business benefit:** AI speed with human judgment. No uncontrolled autonomous
remediation.

### 8. Learns from what actually worked (Resolution Memory)

Every confirmed outcome updates the record: ResolveIQ **learns which fixes
work, when, and under what conditions** — and gets better at ranking over time.
Confirmations and failures both feed back — it never needs manual retraining.

**Business benefit:** it gets smarter the longer you use it, and stays current
as tickets close — no manual retraining.

### 9. Duplicate detection

Near-identical fixes (95%+ match) are **linked as one recurrence, not
re-stored**; 85–95% matches are flagged for a human merge. Duplicated effort is
eliminated at the root.

**Business benefit:** the knowledge base stays **clean and canonical** — one fix
per problem, not five near-copies.

### 10. Multilingual retrieval (trilingual)

A query in **English, Bahasa Malaysia, or Chinese** finds the same best-known
solution — even when it was documented in a different language.

**Business benefit:** built for Malaysia — consultants search in their own
language and still get the right fix, regardless of how it was originally
written.

### 11. Deterministic, explainable scoring (no black box)

The ranking uses a fixed, auditable scoring formula — semantic match (25%),
error-code match (15%), system/module (15%), environment (10%), historical
success (20%), recency (10%), consultant feedback (5%). **The LLM never
arbitrarily picks the winner**; it's just one stage in a deterministic,
reproducible decision.

**Business benefit:** leadership can audit *exactly* why anything ranked where
it did — reproducible, explainable, defensible. This is the core bullet that
kills the "it's just a RAG chatbot" objection.

### 12. Honest gap detection + escalation (confidence bands)

Three confidence bands: **confident** (answers), **mid** (asks for context),
**weak** (escalates to a human). It never invents certainty when evidence is
weak.

**Business benefit:** the engine "knows when not to guess," which keeps trust
high and prevents wrong answers from causing real damage.

### 13. Access, privacy &amp; currency safeguards

Content that requires restricted access stays restricted (RBAC, phased). **PII
is redacted** before embedding. Content referencing retired systems is
filtered.

**Business benefit:** compliant and safe — it respects access permissions and
never leaks sensitive data into answers.

### 14. Full audit trail

Every recommendation and action is logged with **source, confidence, and
reasoning** — stronger accountability than a manual process.

**Business benefit:** every decision is explainable and reviewable by
leadership.

### 15. Management decision support (dashboard)

The dashboard surfaces **top recurring issue categories and volume trends** —
turning ResolveIQ into management decision support, not just a consultant tool.

**Business benefit:** leadership sees what keeps recurring and fixes root
causes, not just symptoms.

---

## Business impact &amp; ROI

- **Faster resolution:** average time to resolve drops from **~20 minutes to
~3.2 seconds** — an **~83% reduction** on matched cases (novel /
low-confidence cases still take normal investigation time).
- **Less duplication:** ~**15% of incoming issues** are avoidable duplicates —
now caught and merged at the root.
- **Potential annual savings:** a team of 10 consultants handling ~50,000
tickets/year, at ~2.5 min saved/ticket × $50/hr → **$100,000+ in potential
annual savings** (conservative).
- **Low infrastructure cost:** cloud-hosted vector database (Pinecone/Chroma),
pay-per-use, scales automatically as ticket volume grows. No new physical
infrastructure.
- **Connectors:** read-only integration via SAP OData/REST APIs and Microsoft
Graph API for SharePoint.

---

## Phased delivery (de-risks the ask)

- **Phase 1 / MVP:** core retrieval + rule pre-filter + AI judge + threshold +
human review + duplicate detection, respecting source-level access tags.
- **Phase 2:** full nested RBAC mirroring and live system connectors, once core
retrieval is validated.

**Business benefit:** you get value in the first phase with low risk; deeper
permissions and connectors land only after the core is proven.

---

## How it works (short version)

1. **Connect once** — read-only API connections to all four sources (tickets,
 SAP, SharePoint, knowledge bases). No copying.
2. **Continuous learning** — the system keeps learning as new tickets close; no
 manual retraining.
3. **Rule-based pre-filter** — instant, free; removes obvious junk (cancelled
 tickets, empty resolutions).
4. **AI judge** — scores surviving content against a checklist (clear
 resolution? reusable? deprecated tech? PII?) with structured reasoning.
5. **Threshold + human review** — high confidence auto-adds; low confidence is
 discarded; gray-zone cases are flagged for a human.
6. **Duplicate detection** — 95%+ linked as recurrence; 85–95% flagged for
 merge.
7. **Ranked by effectiveness** — solutions scored on relevance **and** how
 often they've worked historically.
8. **Access, privacy, currency** — restricted content stays restricted; PII
 redacted; retired systems filtered.

---

## What sets this apart from a simple RAG chatbot


| ResolveIQ                                                        | Generic RAG chatbot                     |
| ---------------------------------------------------------------- | --------------------------------------- |
| **Outcome-aware**: ranks by what worked historically             | Sorts by similarity only                |
| **Knows when not to guess** (escalates honestly)                 | Always produces an answer, even a guess |
| **Explains every recommendation** (Why Panel)                    | Limited or no reasoning                 |
| **Deterministic, auditable scoring** (LLM can't pick the winner) | Black-box / arbitrary selection         |
| **Learns from outcomes** (Resolution Memory)                     | Static knowledge base                   |
| **Detects duplicates** to keep the KB clean                      | Duplicates accumulate                   |
| **Human-in-the-loop** with tiered autonomy                       | Black-box auto-answer                   |
| **Respects access permissions &amp; redacts PII**                | May surface restricted/PII content      |


---

## Quick facts

- **Name:** ResolveIQ — AI-Powered Solution Intelligence Engine
- **Challenge:** NTT DATA Challenge (YEI 3.0 Premium)
- **Stack:** Python (FastAPI), React web + chat, cloud-hosted vector database,
multilingual embeddings, outcome-aware ranking.
- **Users:** Enterprise IT support consultants.
- **Slogan:** "Find what worked. Know why. Learn what works next."
- **Mission fit:** helps consultants find and reuse the best-known solution
faster, instead of reinventing it.

