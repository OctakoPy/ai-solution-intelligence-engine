# Demo Query Set — verified behavior

Every query below was run through both **Find a Solution** (`/api/search`) and
**Chat** (`/api/chat/start`) against the Full (78) dataset. Re-run them all at
any time:

```bash
just api                                   # terminal 1
uv run python scripts/demo_sweep.py         # terminal 2
```

The script prints a per-query table, the follow-up turns, a cross-surface
check (the same query must return the same record on both pages), and a
sanity block that fails if an off-topic query ever gets answered.

## Verdict meanings

| Verdict | What the user sees |
| --- | --- |
| `PROCEED` | Direct answer: the record title, its resolution, and its real track record |
| `ask_context` | "Not confident enough" — the amber banner asking for error code / module / environment |
| `escalate_sme` | "No confident match" — declines rather than guessing |

## What the audience actually sees

Every confidence statement is a plain sentence, never a bare percentage. A
composite score is a weighted blend, so quoting "51%" invites a business
reader to misread it as "a 51% chance this is right" while the sentence
around it says the engine will not answer.

| Situation | What is shown |
| --- | --- |
| Perfect history, exact error code | "High confidence - the error code matches exactly, and this fix has worked every time it was tried." |
| Perfect history | "High confidence - this fix has worked every time it was tried." |
| Usually works, exact error code | "Good confidence - the error code matches, and this fix usually works." |
| Related but weak | "Worth reviewing - this is a related record, not a confirmed match." |
| Nothing close enough | "Nothing in the knowledge base matches this closely enough to recommend." |

Track records stay as concrete counts (`worked 8 of 8 times`) because those
are evidence, not a score, and cannot be misread.

The **Why this** panel leads with the reasons in plain English — "The error
code you gave matches this record exactly", "It has worked every time it was
tried" — and the weighted numbers sit behind a **Show scoring detail** toggle
for anyone reviewing the method.

## Recommended demo script

These five beats cover every behavior the product claims. All are verified.

### 1. Clear question → direct answer

> a finance user cannot run SAP FI reports, getting S_RS_COMP authorization error

Finds `TIC-1001` (8 of 8) and answers with the real fix — assign
`Z_FI_REPORT_DISPLAY` in SU01, confirm with SU53, re-login.

### 2. Vague question → asks for context → answers

> finance user cannot open the report

Gets `ask_context`. Then send:

> error code S_RS_COMP, module SAP FICO, environment PROD

Confidence moves **0.452 → 0.727** and it commits to the answer. This is the
strongest demo beat: the engine visibly changes its mind because of what you
told it.

### 3. Wrong fix ruled out → names it → finds another

> out look cannot send email, stuck in outbox

Gets `ask_context` on the sync record. Then send:

> that did not work, still stuck in outbox

The reply **names the record it ruled out** and surfaces `TIC-1019`
"Cannot send emails with large attachments" (25 of 25) instead. The engine
recovered to a correct, proven fix on its own.

### 4. A fix you already tried → honest decline

> sap transaction me23n running slow for finance team

Answers with `TIC-1041` (7 of 7). Then send:

> that did not work, still very slow

The engine says *"Ruling that out: SAP transaction ME23N running slow for
Finance team"* and escalates — it does **not** silently substitute a different
SAP record. There is no second ME23N fix in the index.

### 5. Off-topic → clean decline

> i ran out of milk in my house

Declines at 30%. Also verified: *"what is the weather in london"*,
*"where is a good place to get lunch"*, *"how do i book a dentist appointment"*.

## Full verified table

`PROCEED` answers; `ask` asks for context; `esc` declines. Both surfaces always
return the same record.

| Query | Find | Chat | Record |
| --- | --- | --- | --- |
| a finance user cannot run SAP FI reports, getting S_RS_COMP authorization error | PROCEED | PROCEED | TIC-1001 8/8 |
| finance user cannot open the report | esc | ask | TIC-1001 8/8 |
| *(same + context)* | ask | PROCEED | TIC-1001 8/8 |
| goods receipt posting error in SAP MM, account determination issue | PROCEED | PROCEED | TIC-3011 6/6 |
| sap transaction me23n running slow for finance team | PROCEED | PROCEED | TIC-1041 7/7 |
| the nightly sap batch job for inventory reconciliation keeps short dumping | PROCEED | PROCEED | TIC-1031 6/7 |
| po approval tile missing from fiori launchpad after update | PROCEED | PROCEED | TIC-3006 9/10 |
| my inbox fiori app is not showing approval items for the it operations manager | PROCEED | PROCEED | TIC-1048 9/9 |
| cannot open excel attachment from sap workflow inbox | PROCEED | PROCEED | TIC-1042 11/11 |
| VPN drops after 5 minutes, reconnect fails on Windows 11 | PROCEED | PROCEED | TIC-1008 11/13 |
| user locked out of account after failed login attempts | PROCEED | ask | TIC-1013 45/45 |
| Outlook not syncing new emails | PROCEED | ask | TIC-1017 15/17 |
| cannot access project SharePoint site | PROCEED | ask | TIC-1028 16/18 |
| printer on 3rd floor not responding | PROCEED | ask | TIC-1021 11/13 |
| need additional SAP GUI license for new consultant | PROCEED | PROCEED | TIC-1025 12/12 |
| new employee laptop setup standard procedure | PROCEED | ask | KB_-1037 40/40 |
| cannot get into the site | esc | esc | declines |
| cannot log in to my computer | esc | esc | declines |
| i ran out of milk in my house | esc | esc | declines |

**Find and Chat differ on `ask` vs `PROCEED` by design.** Chat displays a
boosted score for conversational phrasing, so a query can clear the answer bar
there while Find still asks for context. The *record* is always identical, and
the banner always matches the prose.

## Two queries that decline on purpose

- **"recurring idoc processing errors in logistics"** → `SAP-1044`, worked 6 of
  9. A two-thirds success rate is below the trust bar, so the engine asks for
  context rather than presenting it as a fix. Use
  *"goods receipt posting error"* (6 of 6) if you want an SAP MM answer.
- **"custom sap add-on causing session timeouts"** → declines. The only add-on
  record is still `Escalated` in the source data, so it never enters the index.

## Records deliberately not in the index

These categories exist in `data/knowledge.json` but are filtered at ingestion,
so there is nothing to retrieve. That is the pipeline working, not a gap:

| Category | Excluded because |
| --- | --- |
| `compliance` | `quality_flag: junk` — auto-rejected |
| `hr_systems` | `access_level: restricted` — security filter |
| `sap_addons` | `status: Escalated` — no proven fix |

78 records load, 51 index. The Overview "Processed" count shows all 78; the
other three drop out during the pipeline.
