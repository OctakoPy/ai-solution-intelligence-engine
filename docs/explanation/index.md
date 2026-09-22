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
