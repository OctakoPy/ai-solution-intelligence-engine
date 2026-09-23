# Demo Script

A step-by-step demo of the Solution Intelligence Engine, run on the **Full (78)**
dataset. Questions are phrased as a real support agent would type them, and
include failing cases to show honest gap handling.

The knowledge base is **trilingual** — English, Bahasa Malaysia (BM), and
Chinese (中文). An English search surfaces the BM/中文 versions of matching
problems right alongside the English canons; expand any non-English result to
reveal a **BM/中文 badge** and a **Translate to English** button.

Also see the [5-minute walkthrough script](#voiceover-walkthrough-5-min) for a
non-technical voiceover version.

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

**Expected:** No confident match. Nearest look-alikes (e.g. `TIC-1048`,
`sap_fiori`) surface at **~0.56 semantic similarity** — far below the ~0.88 of a
trusted match. No false confidence; the engine escalates to a human.

**Why it's good:** Honest confidence readout instead of a made-up fix. Pilots
the escalate-to-human path.

### 5. Failing case — novel / low confidence (honest gap, second)

> the new quarterly compliance export is coming up and the custom abap program zreport99 keeps erroring. any known fix?

**Expected:** Only nearest neighbors at **~0.59 semantic similarity** (e.g.
`TIC-1047`, `kb_maintenance` — an outdated KB article, not a match).

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

**Expected:** Low-confidence match only (~0.59 semantic similarity to an
outdated KB article, not a real match). System escalates / recommends manual
handling rather than fabricate an answer.

---

## Multilingual showcase

The engine embeds English, Bahasa Malaysia, and Chinese into one vector space.
A single **English** query surfaces the **BM and 中文** translations of matching
problems right alongside the English canons. These appear in **Find a
Solution**, **Chat** candidates, and as a **badge** on the Pipeline ticket while
it animates.

### 1. FI authorization (surfaces BM + 中文 variants)

> user cannot access financial reports in sap, authorization error

**Expected hits:** `TIC-1001` (en), `TIC-2004` (中文), plus other SAP auth
entries. Expand `TIC-2004` → Chinese content + **Translate to English** button
→ swaps to the English title/description/resolution.

### 2. VPN (surfaces BM + 中文 variants)

> vpn keeps dropping and will not reconnect

**Expected hits:** `TIC-1008` (en), `TIC-2005` (中文), `TIC-2002` (BM). Expand a
BM entry (e.g. `TIC-2002`) → Bahasa Malaysia content → **Translate to English**.

### 3. Account lockout (surfaces BM + 中文 variants)

> user locked out of account cannot log in

**Expected hits:** `TIC-1013` (en), `TIC-2006` (中文), `TIC-2003` (BM).

**Demo tip:** For each, expand the non-English result and click **Translate to
English** — it reveals the full English translation instantly (stored in the
dataset, not a live translator).

### Language badges

- **Pipeline:** small `BM` / `中文` badge beside the ticket id while animating.
- **Find a Solution / Chat:** badge next to each non-English result title.
- Expand a non-English result anywhere to get the translate toggle.

---

## Voiceover walkthrough (5 min)

Run on the **Full (78)** dataset. Non-technical narration, dashboard order:

**Overview → Pipeline → Find a Solution → Chat**

Timestamps are targets; adjust to the pacing of your screen recording.

### 0:00 — Overview Page

**[Screen: Overview page, sidebar, dataset set to Full 78]**

"This is the Solution Intelligence Engine. It's a single dashboard where
support teams can see everything the AI has absorbed — all in one place.

Right now we're looking at a full day of work: 78 records processed. That's
78 real problems pulled in from four different IT systems — our ticketing
system, SAP, SharePoint documents, and the internal knowledge base.

Notice these three numbers. Out of 78 records, most got **added** to the
knowledge base so the system can reuse them later. A smaller slice got
**rejected** — those are duplicates the AI caught automatically, so a
consultant never has to solve the same thing twice.

And the speed matters. The average processing time sits at about **3.2
seconds** per record. That's the difference between a user waiting hours for
a fix and getting one in minutes.

Now let me show you how the AI actually decides what to trust."

### ~0:45 — Pipeline Page

**[Screen: switch to Pipeline, press the play button]**

"The Pipeline is where the engine's judgment happens. Watch closely — each
ticket gets run through a three-step gauntlet.

First, a structural check. Does the record have everything a usable solution
needs? Then an AI quality judge reads the actual text and scores its
explanatory quality. And last, a similarity check — is this the same problem
we already solved?

So for 78 records the pipeline **rejects** the near-duplicates the AI was
already confident about, and **flags** the gray-zone cases for a human
consultant to look at. The engine never silently throws anything away — it
just routes it to the right human attention."

### ~1:30 — Find a Solution

**[Screen: switch to Find a Solution, type the FI reports query]**

"Now the fun part. A user calls in: `user can't get into FI reports... getting
not authorized this morning`. I'll find an existing solution.

The engine parses the semantics and finds the most similar problems people
have solved before — instantly. Top hit: `TIC-1001`, a near-identical auth
issue that was **worked 8 out of 8 times**, with a high-confidence readout.

And this is the part I love — I can expand it and get the **why**: a panel
that breaks the confidence score into its weighted signals, shows the prior
success rate (worked 8 of 8), lists the supporting records from other source
systems that corroborate the fix, and flags any caveats. The exact
step-by-step resolution and the system it came from are right below.

Now watch the bottom of the list. The engine is multilingual — that English
query just surfaced Bahasa Malaysia and Chinese translations of the same auth
fix."

### ~2:30 — Chat

**[Screen: switch to Chat, type the refresh follow-up]**

"Finally, the conversational layer. Once I'm on a solution I can keep asking:
`how exactly do i fix the authorization?`. The engine re-ranks its candidates
using the follow-up, and walks me through the role assignment — step by step —
while keeping the full source handy.

No hallucinated answers, no hunting across four systems. Just the fix, the
proof it worked before, and the steps to do it."

### ~3:30 — Honest gap handling

**[Screen: Find a Solution, type the `zreport99` query]**

"Because trust matters most when the answer ISN'T in the knowledge base. Try
something brand new: `the custom abap program zreport99 keeps erroring`.

No confident match. The engine doesn't bluff — it shows its closest
look-alikes at full confidence, all graded well below the trusted threshold,
so the human knows this needs a manual fix and an escalation instead of a
made-up answer."

### ~3:55 — Close

**[Screen: back on Overview]**

"That's the Solution Intelligence Engine — structured ingestion, honest
confidence, multilingual retrieval, and a human in the loop, so support teams
solve once and reuse forever."

---

## What you can test — outcome-aware context (Find a Solution)

Set the dataset to **Full (78)**, open **Find a Solution**, and run these
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
