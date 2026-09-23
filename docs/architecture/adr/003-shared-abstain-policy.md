---
tags:
  - policy
  - retrieval
---

# ADR-003: One shared abstain policy across Find, Chat, and evaluation

| | |
| ---| ---|
| **Status** |  🟢 Accepted |
| **Created**  | 2026-09-23 |
| **Last Updated**  | 2026-09-23 |
| **Deciders** | Octako |
| **Tags** | policy, retrieval |

---

## Context

The engine makes two kinds of promises at once. It ranks candidates by an
outcome-aware confidence score (`rank_results`, seven weighted deterministic
signals), and it promises to "know when not to guess": when evidence is weak,
the system changes the action instead of inventing certainty. The first
promise is enforced by a single shared ranking path. The second was not:
before this decision, abstain thresholds lived in three places with slightly
different values and scales — chat reply wording (0.75 / 0.90 on a boosted
display scale), the pilot evaluation's `ABSTAIN_THRESHOLD` (0.75 on core
confidence), and no policy at all on the Find a Solution API, which returned
candidates unconditionally.

The system runs without external LLM calls. Every user-visible number and
sentence must be deterministic and auditable, and every surface that shows a
confidence must agree with the guidance it gives.

## Problem Statement

Where should the abstain thresholds, the decision logic, and the
next-best-action payloads live so that Find a Solution, Chat, and the
evaluation framework abstain identically — and so the guidance can never
contradict the confidence number displayed on screen?

## Options Considered

Drivers: **consistency** (all surfaces abstain identically), **UI agreement**
(guidance matches the displayed number), **auditability** (one place to tune,
deterministic wording), **eval validity** (the pilot evaluation must measure
the same policy users experience), **effort**.

|  Option  | Description | Consistency | UI agreement | Auditability | Eval validity | Effort | Overall score | Notes |
|----------|-------------|-------------|--------------|--------------|---------------|--------|---------------|-------|
| **Weight**   | - | 3 | 3 | 2 | 2 | 1 | - | - |
| **A. Shared core policy module** | `solution_intelligence/policy.py` owns thresholds + `decide()`; API maps verdicts per surface | ✅ | ✅ | ✅ | ✅ | ✅ | 33 | One source of truth; per-surface display mapping is explicit |
| **B. Policy in the API layer** | `apps/api/policy.py` owns everything; eval keeps its own constant | ⚠️ | ⚠️ | ⚠️ | ❌ | ✅ | 20 | Eval drifts from the product policy; core stays policy-free |
| **C. Per-surface policies** | Chat keeps its bands; search gets its own | ❌ | ⚠️ | ❌ | ❌ | ⚠️ | 13 | Exactly the pre-#18 state; guarantees drift |

✅ = 3 (good), ⚠️ = 2 (acceptable), ❌ = 1 (poor)

## Decision Outcome

We will use **Option A**: a shared core policy module
(`solution_intelligence/policy.py`) that owns the thresholds
(`ABSTAIN_THRESHOLD = 0.75`, `CONFIDENT_THRESHOLD = 0.90`), the `decide()`
verdict (`proceed` / `ask_context` / `escalate_sme`), and the deterministic
next-best-action payloads. Chat's reply bands and the evaluation's
`ABSTAIN_THRESHOLD` are aliases of these constants, so a drift breaks a test
instead of silently splitting the product's behavior.

One refinement proved necessary during verification: the verdict must be
computed **per surface, from the score that surface actually displays**
(Find shows the outcome-aware confidence; Chat boosts similarity by 1.25×).
A policy evaluated on a different number than the one on screen produced
absurd UIs — an 84% hit carrying a "not confident" banner while a 51% hit
carried none. The invariant is now explicit in `apps/api/policy.py`:
**guidance matches the displayed number**, and a regression test walks both
surfaces asserting it.

## Consequences

* Good, because tuning the policy is a one-line change that every surface
  obeys, and the evaluation measures exactly what users experience.
* Good, because the context-trap detector (`is_context_trap`: matched cue +
  conflicting cue ⇒ "verify root cause" caveat) rides the same module and is
  testable without the API layer.
* Bad, because the core package now contains presentation-flavored wording
  (the payload messages), which the demo stance requires to be deterministic.
* Unknowns/risks: the display scales themselves (the 1.25× chat boost) are a
  demo affordance; if the boost is ever removed, `evaluate_policy(surface=...)`
  collapses to a single call path — the invariant survives, only the mapping
  simplifies.

## Confirmation

* `tests/unit/test_policy.py` pins the bands and asserts
  `evaluate.ABSTAIN_THRESHOLD == policy.ABSTAIN_THRESHOLD` (sync guard).
* `tests/unit/test_api.py::test_policy_matches_displayed_score_on_both_surfaces`
  walks real API responses asserting guidance agrees with the displayed
  percentage on both surfaces.
* Docs: the "Knows when not to guess" section in `docs/explanation/index.md`
  documents the bands; changes to them must update that table.

## Links

| Type | Links |
| -----| ------|
| **ADRs**   | ADR-001 (process) |
| **Issues** | #18 (shared abstain policy), #15 (outcome-aware ranking), #17 (why panel) |
| **PRs**    | #26 (policy), #24 (shared ranking), #25 (evidence panel) |
