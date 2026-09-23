# Explanation

Why the engine works the way it does — the reasoning behind the accessible
behavior you see in the tutorials.

## The problems it solves

Support consultants lose hours searching four disconnected systems, re-solving
issues that were already solved, and trusting answers they can't verify.

- **Siloed knowledge** — tickets, SAP notes, SharePoint documents, and KB
  articles each live in their own system with their own vocabulary.
- **Unreliable answers** — search returns fragments, not proof; nothing tells
  you whether a fix actually worked.
- **Duplicate work** — the same root cause is solved over and over because
  nobody recognizes the near-duplicate.

## How the engine addresses each

- **Unified index** — every record is normalized into one schema and embedded
  into a shared multilingual vector space, so a single query reaches across
  all four systems.
- **Honest confidence** — each match combines semantic similarity with the
  record's *worked count* (how often it resolved before) into a transparent
  0–100% score, alongside the source, the exact resolution, and the reasoning.
- **Duplicate defense** — during ingestion, near-duplicates are routed to a
  human review queue with the AI's reasoning attached instead of being
  silently added or discarded.

## The ingestion judgment chain

Every record passes a three-stage gauntlet:

1. **Stage 1 — structural filter.** Does the record have the fields a usable
   solution needs? Anything missing essentials is rejected early.
2. **AI quality judge.** A language model scores the record's explanatory
   quality (reproducibility, completeness, and clarity of the resolution).
   High judges pass; low judges are flagged or rejected.
3. **Embedding-based duplicate check.** New records are compared against the
   accepted index; near-duplicates are flagged for human review (never
   auto-committed), and true duplicates are rejected.

## Confidence: not just similarity

Every match carries an outcome-aware confidence score: a deterministic,
auditable weighted sum of seven signals.

| Signal | Weight | Source |
| --- | --- | --- |
| Semantic similarity | 0.25 | how close the incident text is to the record |
| Error-code match | 0.15 | exact match of the incident error code |
| System / module match | 0.15 | incident module vs the record's module |
| Environment match | 0.10 | environment equality (PROD, UAT, ...) |
| Historical success rate | 0.20 | worked / attempted |
| Recency decay | 0.10 | how fresh the record is (half-life model) |
| Consultant feedback | 0.05 | thumbs up / down from the UI |

The weights are module-level constants in `retrieval.py` that sum to 1.0, so
the score is explainable without calling a model. The three match signals only
fire when an incident supplies structured context (error code, module,
environment); without context they contribute nothing instead of guessing.

Because a failed fix lowers the success-rate signal and a mismatched
environment zeroes the environment signal, a record that merely *looks*
similar — but failed before or belongs to a different context — cannot win on
similarity alone. Search results are ranked by this outcome-aware confidence
score (not by raw similarity), and the readout is always shown, so a
low-confidence match looks low-confidence instead of looking like an answer.

## Knows when not to guess

Ranking honestly is only half of trust; the other half is changing the
*action* when evidence is weak instead of inventing certainty. One shared
abstain policy (`solution_intelligence/policy.py`) decides this for every
surface — Find a Solution, Chat, and the pilot evaluation:

| Confidence band | Engine behavior | `next_best_action` |
| --- | --- | --- |
| ≥ 0.90 | Answers confidently | none |
| 0.75 – 0.90 | Offers nearest matches, asks for missing context | `ask_context` — names the missing error code / module / environment fields |
| < 0.75 | Will not offer a fix | `escalate_sme` — hands off to a subject-matter expert, naming the nearest look-alike |

The API attaches the resulting `next_best_action` payload to both
`/api/search` and `/api/chat` responses, and the UI renders it as an amber
banner. Because the chat thresholds and the evaluation's `ABSTAIN_THRESHOLD`
are aliases of the same constants, tuning the policy is a one-line change
that every surface obeys.

The policy also detects the **context trap**: when a record matches one
cue (say the error code) but conflicts on another that the incident
supplied (say PROD vs UAT), its why panel carries a "verify root cause —
evidence may be from a different context" caveat. The same error code on a
different environment is usually a different root cause, and the engine
says so rather than letting similarity hide it.

## Measuring whether it works: the pilot eval

Confidence claims are only meaningful if they are measured. The evaluation
framework (`evaluate.py`, run with `just eval`) scores the ranking against a
labeled set of queries derived from the demo dataset, comparing three modes:
raw similarity (the old behavior), outcome-aware confidence without incident
context, and the full outcome-aware ranking with context.

Three results matter:

- **Retrieval quality** — top-1 / top-3 success and mean reciprocal rank.
  On the labeled set, context-ful ranking lifts top-1 from 75% to 100% while
  similarity-only and context-less modes tie at 75%: the three context cases
  are exactly where similarity alone picks the wrong record.
- **Calibration** — confidence on hits should sit far above confidence on
  misses and on the honest-gap cases. If a high score ever landed on a gap,
  the abstain policy (0.75 bar) would be lying; the eval's abstain-precision
  metric catches that.
- **The context trap** — the M8149 UAT case is graded explicitly: with UAT
  context the UAT record must rank first, not the PROD look-alike. Similarity
  fails this check (it ranks by text closeness, and the two records are
  nearly identical in text); outcome-aware ranking passes it.

The eval is deterministic for a fixed dataset and embedder, so any change to
weights, signals, or ranking logic shows up as a before/after diff in the
report rather than as a vibes-level impression.

## The learning loop: Resolution Memory

A confidence score is only honest if it changes when reality disagrees with
it. Resolution Memory closes that loop: every recommendation can be
confirmed as worked or not worked, the outcome is appended to a persistent
log, and the affected record's `worked_count` is adjusted on the next
ingest or search. Because `worked_count` feeds the success-rate signal in
the confidence score (weight 0.20), a confirmed failure demotes a candidate
and a confirmed success boosts it — positive and negative learning from one
mechanism, with no retraining.

The log is the single source of learned state. Deltas are always recomputed
from the log against each record's pristine base counts, so the loop is
idempotent (re-ingesting the static dataset never double-counts) and
resetting is just deleting `data/resolution_memory.json`.

## Multilingual retrieval without translation

Tickets arrive in English, Bahasa Malaysia, and Chinese. Instead of translating
everything to one language, the engine embeds all three into a single vector
space using a multilingual model, so an English query naturally surfaces
matching BM and 中文 records. Non-English records also carry a stored English
translation for the **Translate to English** toggle in the UI.

## Honest gap handling

For a genuinely new issue, the closest index neighbors land far below the
confidence threshold. The engine surfaces them anyway — clearly graded — with
an explicit escalate-to-human recommendation. Fabricating a confident fix is
treated as worse than admitting the gap.

## Design principles

- **Trust before speed.** Every answer shows its source, similarity, confidence,
  and history.
- **Human in the loop.** Anything gray (near-duplicates, low-quality) is
  surfaced for review, never auto-applied.
- **Transparent pipeline.** The pipeline animation shows exactly what was
  accepted, flagged, and rejected — and why.
