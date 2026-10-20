# Demo Script

A step-by-step demo of the Solution Intelligence Engine, run on the whole **104-record**
dataset. Questions are phrased as a real support agent would type them, and
include failing cases to show honest gap handling.

The knowledge base is **four-language** — English, Bahasa Malaysia (BM),
Chinese (中文), and Japanese (日本語). An English search surfaces the
non-English versions of matching problems right alongside the English canons;
expand any non-English result to reveal a **language badge** and a **Translate
to English** button.

Also see the [recorded walkthrough](#recorded-walkthrough-3-min) for the
non-technical narration version.

---

## Resolution Memory (Overview) — seeded demo state

The **Overview** page's *Resolution Memory* panel is seeded for the demo. On
**every API restart** the outcome log resets to a fixed seed of **14
outcomes** — **11 worked / 3 rejected** across **14 knowledge records** (79%
success rate) — with the most recent outcome less than an hour old, so the
panel (donut, tallies, "last outcome … ago") is populated on the first frame
of every run.

- Live thumbs recorded during the demo **add on top** of the seed; the next
  restart wipes back to the seed.
- The seed deliberately avoids every record this script quotes (`TIC-1001`
  stays **8/8**, and the VPN, auth, multilingual, chat, honest-gap, and
  `M8149` context records keep their scripted track records), so scripted
  rankings are unaffected.
- After recording an outcome live, **hard-refresh Overview** (Ctrl+R) — the
  dashboard query caches for 30 seconds.

---

## Find a Solution

### 1. Canonical high-confidence match (best case)

> user can't get into FI reports in sap fico, getting not authorized this morning

**Where it lands:** `TIC-1001` — high-confidence canonical, worked 8/8.

**Why it's good:** Clean resolution (SU01 role assign + SU53 confirm), high
trust score. Shows the system's strongest case.

### 2. Near-duplicate variant (generalizes beyond exact wording)

> employee blocked from CO cost center controlling reports, auth error on the transaction

**Where it lands:** `TIC-1004` — near-duplicate variant of the same auth group.

**Why it's good:** Different module (CO vs FI), re-worded, but the system
catches it as a variant of the known `sap_fi_auth` problem. Shows it generalizes.

### 3. Non-SAP / cross-domain (broader coverage)

> vpn keeps dropping after a few mins on windows 11 and wont reconnect

**Where it lands:** `TIC-1008` — high-volume auto-resolve root.

**Why it's good:** Proves coverage isn't SAP-only. Fast, confident, reusable.

### 4. Failing case — novel / low confidence (honest gap)

> the po approval tile is missing from fiori launchpad for a few users after this weeks update

**Expected:** No confident match. Nearest look-alikes (e.g. `TIC-1107`,
`sap_fiori`) surface at **~0.43 semantic similarity** — far below the 0.60
abstain threshold. No false confidence; the engine escalates to a human.

**Why it's good:** Honest confidence readout instead of a made-up fix. Pilots
the escalate-to-human path.

### 5. Failing case — novel / low confidence (honest gap, second)

> the new quarterly compliance export is coming up and the custom abap program zreport99 keeps erroring. any known fix?

**Expected:** Only nearest neighbors at **~0.41 semantic similarity** (e.g.
`TIC-1001`, an SAP authorization record — a look-alike, not a match).

**Why it's good:** Reinforces that novel/undocumented issues get an honest
"low confidence, escalate to human" answer, never a confident fabricated fix.

---

## Chat with the Engine

### 1. Concrete troubleshooting (uses a known solution)

> a finance user cant run sap fi reports this morning, getting an auth error. what should i do?

**Expected:** Leads to the `Z_FI_REPORT_DISPLAY` role fix, SU53 trace, re-login.

### 2. Root-cause / diagnostic

> the nightly sap batch job for inventory reconciliation keeps short dumping. how do i fix it?

**Expected:** Points at `TIC-1031` — db lock timeout; reschedule + retry logic.

### 3. Policy / best-practice (knowledge base, not just tickets)

> how do i set up a laptop for a new employee, whats the standard?

**Expected:** Pulls the authoritative KB article `KB_-1037` (onboarding
standard). Shows cross-source retrieval (tickets + SAP + SharePoint + KB).

### 4. Failing case — novel / no confident match (honest gap)

> the new quarterly compliance export is coming up and the custom abap program zreport99 keeps erroring. any known fix?

**Expected:** Low-confidence match only (~0.41 semantic similarity, below the
0.60 abstain threshold). System escalates / recommends manual handling rather
than fabricate an answer.

---

## Multilingual showcase

The engine embeds English, Bahasa Malaysia, Chinese, and Japanese into one
vector space. A single **English** query surfaces the **BM / 中文 / 日本語**
versions of matching problems right alongside the English canons. These appear
in **Find a Solution**, **Chat** candidates, and as a **badge** on the Pipeline
ticket while it animates.

### 1. FI authorization (surfaces BM + 中文 + 日本語 variants)

> user cannot access financial reports in sap, authorization error

**Expected hits:** `TIC-1001` (en), `TIC-2001` (BM), `TIC-2004` (中文),
`TIC-3020` (日本語) — three translations of the same auth canon. Expand
`TIC-2004` → Chinese content + **Translate to English** button → swaps to the
English title/description/resolution.

### 2. VPN (surfaces BM + 中文 variants)

> vpn keeps dropping and will not reconnect

**Expected hits:** `TIC-1008` (en), `TIC-2002` (BM), `TIC-2005` (中文). Expand a
BM entry (e.g. `TIC-2002`) → Bahasa Malaysia content → **Translate to English**.

### 3. Account lockout (surfaces BM + 中文 + 日本語 variants)

> user locked out of account cannot log in

**Expected hits:** `TIC-1013` (en), `TIC-2003` (BM), `TIC-2006` (中文),
`TIC-3022` (日本語).

**Demo tip:** For each, expand the non-English result and click **Translate to
English** — it reveals the full English translation instantly (stored in the
dataset, not a live translator).

### Language badges

- **Pipeline:** small `BM` / `中文` / `日本語` badge beside the ticket id while
  animating.
- **Find a Solution / Chat:** badge next to each non-English result title.
- Expand a non-English result anywhere to get the translate toggle.

---

## Recorded walkthrough (~3 min)

The current cut is a single continuous take (**3:04**), driven by
`apps/web/tests/e2e/demo.spec.ts` and narrated by
[`demo-narration.srt`](demo-narration.srt). Every query below is the exact
string the recording types, so this section cannot drift from the video.

Dashboard order: **Overview → Pipeline → Find a Solution → Chat → Overview**

### 0:00 — Overview

**[Screen: Overview, whole 104-record corpus already loaded — there is no
dataset selector]**

"Support teams handle hundreds of incidents every day. Most were solved
before. The knowledge just isn't connected. So the same fault gets diagnosed
twice."

The status card reads **104 processed · 79 added · 21 rejected · 4 flagged ·
3.2s average** — the four sources (service desk, SAP, SharePoint, knowledge
base) ingested in one pass.

### 0:13 — Ingestion scale

"One hundred and four records, from four real systems. The service desk. SAP.
SharePoint. And the knowledge base."

### 0:20 — Pipeline

**[Screen: Pipeline, press Start]**

"Three checks per record. Restricted data never indexed."

(The three checks are structural, an AI quality judge, and a near-duplicate
similarity gate. 79 records are added, 21 rejected as duplicates, and 4
flagged for a consultant — nothing is silently discarded.)

### 0:28 — Find: the context trap

**[Screen: Find a Solution]**

Search: `goods receipt posting error account determination not found` — the
`TIC-3011` canonical appears.

Open **Incident details (optional)** and enter `M8149` · `SAP MM` · `PROD`,
then search again. Three green **✓ badges** light up (Error code / System /
Environment).

"Now the interesting part. Same code, test environment. A different root
cause. That's the trap it avoids."

Change Environment to `UAT` and search: `TIC-3012` takes over as the top hit.

### 0:52 — Find: four languages

Clear the incident detail, then search:
`user cannot access financial reports in sap, authorization error`

`TIC-1001` (en), `TIC-2001` (BM), `TIC-2004` (中文), and `TIC-3020` (日本語)
appear together. Open the Chinese card and press **Translate to English**.

"English, Malay, Chinese, and now Japanese. Translate the Chinese one and
it's the same fix."

### 1:09 — Find: consultant vocabulary, and an honest decline

Clear again, then search:
`production order will not create component allocation incomplete`

Top hit `TIC-1108` — **worked 12 of 12**.

Then search: `nightly mrp background job failing after release update`

`TIC-1106` (**7 of 9**) is below the trusted floor, so the engine shows
**Check not satisfied** rather than recommend it. Same category, different
record history.

Optionally open **Show scoring detail** on a result — the confidence readout
breaks into weighted signals, prior success, and corroborating records.

### 1:32 — Chat: a plain question

**[Screen: Chat]**

Ask: `I forgot my password and cannot log in to my computer` — answered
directly, **worked 45 of 45**.

### 1:44 — Chat: too vague, so it declines

New chat, ask: `finance user cannot open the report`

**Check not satisfied**, and no ticket numbers or success counts are shown as
evidence for a recommendation that was not made.

Then add what you know: `error code S_RS_COMP, module SAP FICO, environment
PROD` — now it commits, **worked 8 of 8**. Nothing changed but the evidence.

### 2:09 — Chat: the first fix failed

New chat, ask: `my email is not arriving`, then: `that did not work, still
nothing`

It rules that fix out (`Ruling that out: Outlook not syncing new emails`) and
offers a different one (`Cannot send emails with large attachments`) instead
of repeating itself.

### 2:32 — Chat: not only troubleshooting

New chat, ask: `a new starter needs a laptop for their first day` — it pulls
the official **New Employee Laptop Setup** standard procedure.

### 2:46 — Chat: something it should not answer

New chat, ask: `i ran out of milk in my house` — no match exists, so it
declines. That refusal is the feature.

### 2:58 — Close

**[Screen: back on Overview, Resolution Memory panel]**

"Two ways in. Both transparent. Both say when they don't know."

---

## What you can test — outcome-aware context (Find a Solution)

Open **Find a Solution** and run these
scenarios. Use the **Incident details (optional)** panel to add an error code,
system, and environment; matched details appear as green **✓ badges** on the
result cards (Error code / System / Environment) and are reflected in the
confidence readout.

### 1. Exact context match — the M8149 canonical fix

- Query: `goods receipt posting error account determination not found`
- Incident details: `M8149` · `SAP MM` · `PROD`

**Expected:** `TIC-3011` "SAP MM goods receipt posting error - account
determination not found M8149" ranks first with **✓ Error code ✓ System ✓
Environment** badges and the highest confidence. Expand it to see the OBYC
account-determination fix.

### 2. Context trap — same error code, different environment

Same query, same error code and system, but change the environment to `UAT`:

- Incident details: `M8149` · `SAP MM` · `UAT`

**Expected:** `TIC-3012` "M8149 goods receipt posting error in UAT sandbox"
rises to the top with **✓ Error code ✓ System ✓ Environment**. The `PROD`
record (`TIC-3011`) now drops the **Environment** badge — the engine is
signalling that this is the *same error code but a different root cause*, so
the PROD fix should not be applied as-is. This is the "context trap" the
engine is designed to catch.

### 3. Partial match — system matches, environment does not

- Query: `goods receipt posting error account determination not found`
- Incident details: `M8149` · `SAP MM` · (no environment)

**Expected:** Both `M8149` records show **✓ Error code ✓ System** badges, with
no Environment badge on either — the engine is explicit that it cannot confirm
the environment, rather than guessing.

### 4. No context — text-only baseline

- Query: same as above, with **Incident details** cleared.

**Expected:** No badges at all, and overall confidence is lower than with
matching context (the semantic similarity and historical success signals still
work, but the match signals contribute nothing). Run this first, then repeat
scenario 1 to watch the confidence jump.

Also try the SAP authorization cluster: search
`authorization error on financial reports` with error code `S_RS_COMP` —
without context, `TIC-1001` (FICO) and `TIC-1004` (CO) carry no badges and
rank by text; add `SAP CO` as the system and the CO record climbs, showing
that *same error code, different module* is treated as a different case.
