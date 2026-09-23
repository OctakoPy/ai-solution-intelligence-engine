# Verification Script

A replicable click-through flow that verifies the engine's trust behaviors
end to end — **proven fixes win**, **every answer explains itself**, and
**the engine knows when not to guess**. Every expected result below was
captured from the real API; percentages may vary by ±1 point between
machines (embedding rounding), but the behavior — what wins, what the
banner says, which caveats appear — is deterministic.

Use it two ways:

- **Verification** — run it top to bottom after setting up; every step has a
  concrete expected result you can check off.
- **Demo** — each section is a self-contained 1–2 minute story with a
  one-line "point of this step" you can say out loud.

## Setup (5 minutes, once)

```bash
uv sync --all-groups && npm install   # if not already installed
just dev                              # API on :8004, web on :5179
```

Open **http://localhost:5179**.

1. In the left sidebar, set dataset size to **Full (78)**.
2. **Reset the learning log (recommended before a demo):** delete
   `data/resolution_memory.json` and restart `just dev`. The log is runtime
   learning data (gitignored), so a fresh start makes Section 5 exact:
   TIC-1001 shows **8/8** until *you* act on it.
3. All demo queries below are copy-paste strings — exact wording matters,
   because the expected results were captured with them.

> Fast, code-only variant: every step has an equivalent `POST` to
> `http://localhost:8004` (see `apps/api/routes/search.py` for the shape).
> The UI flow is the primary script; the API is the audit trail.

---

## 1. Proven fixes win (issue #15)

**Go to:** Find a Solution

**Type:** `user cannot access FI reports in SAP, authorization error`

| What to do | What you should see |
| --- | --- |
| Read the top result | **TIC-1001** is #1 with a **51%** badge. Lower matches (TIC-1005, SAP-1005, TIC-1004) sit below it. |
| Click **View Details** on TIC-1001 | The **Prior success** row reads **Worked 8 of 8 times (100%)** — the outcome history that put it on top. |

**Point of this step:** the top of the list is the fix that *worked before*,
not merely the one with the most similar words — and the number you see is
the number it was ranked by.

---

## 2. Why this — every answer explains itself (issue #17)

Still on the TIC-1001 detail expansion, look at the gray **WHY THIS** panel:

| What to do | What you should see |
| --- | --- |
| **Score breakdown** | Only contributing signals, each with its weighted points — roughly `Text similarity +0.26`, `Historical success +0.20`. No `+0.00` rows. |
| **Prior success** | `Worked 8 of 8 times (100%)` with a green check. |
| **Evidence** | *Absent* for TIC-1001 — the section only appears when a second record corroborates the fix. |
| **Caveats** | One amber line: *Unverified record: no linked recurrence in another source system corroborates this fix yet.* |

**Cross-record evidence — type:** `password reset` → expand the top hit
(**TIC-1014**).

| What to do | What you should see |
| --- | --- |
| **Evidence** section | Two records: **TIC-1014** (self, first) and **TIC-1015** — the same issue captured in another ticket — each with its own `45/45 worked`. |
| **Caveats** | No "Unverified record" line: the duplicate-group peer corroborates it. |

**Point of this step:** no black box — every recommendation carries the math
behind its score, its track record, and the records that back it up.

---

## 3. Knows when not to guess (issue #18)

**Type:** `the custom abap program zreport99 keeps erroring`

| What to do | What you should see |
| --- | --- |
| Look **above the results** | An amber banner: **"Knows when not to guess — escalate"** with *No historical record is a confident match (best: 41%). Escalate to a subject-matter expert instead of applying a guess.* The number in the banner matches the top card's 41%. |
| Read the results | They are still listed — but as look-alikes for a specialist, not as an answer. The banner is what changes the *action*. |
| **Switch to Chat** and send the same query | The assistant reply refuses to guess **and** the same amber banner appears under the message. The top source card shows **60%** (chat's display scale is boosted to stay consistent with Find), still below the band. |

**Point of this step:** when evidence is weak, the engine changes the action
— it hands off to a human instead of inventing certainty.

---

## 4. The context trap — same error code, different root cause

**Go to:** Find a Solution → expand **Incident details (optional)**

**Type:** `goods receipt posting error`, and set context to
error code **M8149**, system **SAP MM**, environment **PROD** → Search

| What to do | What you should see |
| --- | --- |
| Read the top result | **TIC-3011** at **84%** — the PROD root cause wins in its own environment. The banner says *Not confident enough to recommend a fix, even with the full incident context…* (mid-band, context already complete). |
| Change environment **PROD → UAT**, search again | **TIC-3012** — a *different root cause* — takes the top spot at **80%**. |

**The trap payoff — expand TIC-3011 (the PROD record) in the UAT result
list.** In its WHY THIS panel:

| What to do | What you should see |
| --- | --- |
| **Caveats** | A second amber line: *Verify root cause before applying: this record matches part of your incident context but conflicts on environment — evidence may be from a different context.* |
| **Green signal badges** on the card | Still show *Error code match* — the trap is that one cue matches while another contradicts. |

**Point of this step:** the same error code in a different environment is
usually a different root cause. The engine says so instead of letting
similarity hide it — this is the demo's most convincing moment.

---

## 5. The learning loop — outcomes feed back into ranking

Still on Find a Solution, query from Section 1:

`user cannot access FI reports in SAP, authorization error`

| What to do | What you should see |
| --- | --- |
| On TIC-1001's card, click **No** under *Did this work?* | The badge flips to *Marked failed · engine learned (N outcomes)*. |
| Search the same query again | TIC-1001 now shows **8/9** in Prior success, and its badge drops **51% → 48%**. |
| Click **Yes**, search again | Back to **9/9** and the badge recovers toward 51%. |
| Restart `just dev`, search again | The learned counts persist — outcomes are stored in `data/resolution_memory.json`, applied as recomputed deltas. |

**Point of this step:** confirmed outcomes change future ranking — negative
learning demotes, positive learning recovers. Delete the log file to reset.

---

## 6. Trilingual retrieval (bonus)

**Type:** `Pengguna tidak boleh buka laporan FI dalam SAP, ralat kebenaran`
(Bahasa Malaysia)

| What to do | What you should see |
| --- | --- |
| Read the result list | English **TIC-1001** ranks first, with Bahasa Malaysia (TIC-2001) and Chinese records alongside; non-English cards carry a language badge and a **Translate to English** button in the details. |

**Point of this step:** one shared embedding space — a query in any
supported language surfaces the right fix in any other.

---

## One-minute version (elevator demo)

1. Search the FI authorization query → *proven fix wins, 8/8 worked*.
2. Expand it → *WHY THIS: score math + track record + caveats*.
3. Search `zreport99` → *amber banner: escalate, won't guess*.
4. Trap: `goods receipt posting error` + M8149 in PROD, then UAT →
   *different root cause wins + "verify root cause" caveat*.

## Checks the CI runs so you don't have to

This script mirrors the automated tests: ranking determinism and
failed-vs-proven ordering (`tests/unit/test_ranking.py`), why-panel payload
shape (`tests/unit/test_api.py`), policy bands and the display-agreement
invariant (`tests/unit/test_policy.py`,
`test_policy_matches_displayed_score_on_both_surfaces`), and UI rendering
(`apps/web/src/components/ui/__tests__/why-panel.test.tsx`). If a step above
surprises you, the corresponding test is where to look first.

## Links

- [Demo Script (narrative walkthrough)](demo-script.md)
- [How the engine grades, embeds, and trusts records](../explanation/index.md)
- [ADR-003: shared abstain policy](../architecture/adr/003-shared-abstain-policy.md)
