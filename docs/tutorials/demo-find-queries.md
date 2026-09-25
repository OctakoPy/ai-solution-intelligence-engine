# Find a Solution — demo queries

Find a Solution is the **precision** surface. Chat is for conversation; Find
is where you prove retrieval is exact. Use technical language here — that is
the point of this page. The Incident details panel is what Find does that Chat
does not: it matches structured facts, not just wording.

All examples verified against the running system. Re-run the whole set with:

```bash
just api
uv run python scripts/demo_sweep.py
```

---

## 1. Exact match with the Incident details panel — the headline beat

Open **Incident details (optional)** and fill in all three fields.

| Field | Value |
| --- | --- |
| Query | `goods receipt posting error account determination not found` |
| Error code | `M8149` |
| System / module | `SAP MM` |
| Environment | `PROD` |

**Result:** `TIC-3011` — *SAP MM goods receipt posting error - account
determination not found M8149*

All three green badges light up — **Error code match**, **System / module
match**, **Environment match** — and confidence jumps from **0.48 to 0.88**.
That is the difference between "these words look similar" and "this is your
record".

---

## 2. The context trap — the best beat in the whole demo

Keep the same query and all three fields. Now change **one** thing:

| Field | Value |
| --- | --- |
| Query | `goods receipt posting error account determination not found` |
| Error code | `M8149` |
| System / module | `SAP MM` |
| Environment | `UAT` ← changed |

**Result changes to:** `TIC-3012` — *M8149 goods receipt posting error in UAT
sandbox*

Same error code. Same system. Different environment, **different root cause**
and therefore a different fix. A keyword search cannot do this, and it is the
clearest possible answer to *"why not just use Google?"*

If you then set the environment back to `PROD`, `TIC-3011` comes straight
back. That round trip is worth doing live.

---

## 3. Authorization cluster — one problem, several records

| Query | Top result | Note |
| --- | --- | --- |
| `user cannot access FI reports in SAP, authorization error` | `TIC-1001` (8/8) | The canonical fix |
| `employee blocked from CO cost center reports, auth error` | `TIC-1004` (5/5) | Same problem, CO module, but it asks for context first |
| `authorization error on financial reports` + error code `S_RS_COMP` | `TIC-1001` | Exact error code match |

The middle one is a good beat: it finds the right CO record, then asks rather
than assuming. Fill in the Incident details and it commits.

---

## 4. Multilingual — one English query, three languages

This is the beat that used to be broken. Type an **English** query and the
same answer appears in English, Bahasa Malaysia, and Chinese, all within the
five visible cards:

| Query | Cards you see |
| --- | --- |
| `user cannot access financial reports in sap, authorization error` | `TIC-1001` en, `TIC-2004` **zh**, `TIC-2001` **bm** |
| `vpn keeps dropping and will not reconnect` | `TIC-1008` en, `TIC-2002` **bm**, `TIC-2005` **zh** |
| `user locked out of account cannot log in` | `TIC-1013` en, `TIC-2006` **zh**, `TIC-2003` **bm** |

Each non-English card carries a **BM** / **中文** badge. Open one and click
**Translate to English** to switch the whole entry — title, description and
resolution — into English instantly.

Do not demo the offline story here: an unrelated question such as
`i ran out of milk in my house` correctly returns no confident match. Show
that separately if you want the honesty beat.

---

## 5. Technical queries that answer immediately

Good fillers if you need a few seconds on screen:

| Query | Top result | Track record |
| --- | --- | --- |
| `VPN drops after 5 minutes, reconnect fails on Windows 11` | `TIC-1008` | 11 of 13 |
| `the nightly sap batch job for inventory reconciliation keeps short dumping` | `TIC-1031` | 6 of 7 |
| `cannot open excel attachment from sap workflow inbox` | `TIC-1042` | 11 of 11 |
| `recurring idoc processing errors in logistics` | `SAP-1044` | 6 of 9 — asks for context, on purpose |
| `SAP transaction ME23N running slow for Finance team` | `TIC-1041` | 7 of 7 |

---

## 6. Queries that correctly refuse

Use these to show restraint. All decline with *"Nothing in the knowledge base
matches this closely enough to recommend."*

| Query | Why it declines |
| --- | --- |
| `the quarterly compliance export custom ABAP program keeps erroring` | Real-sounding IT problem, no proven record for it |
| `i ran out of milk in my house` | Obviously nothing to do with IT |
| `where is a good place to get lunch` | Same |

The first is the strongest: a plausible enterprise problem with no answer in
the knowledge base, and the engine says so instead of inventing one.

One clarification: an error code on its own (`M8149`, or `M8149` in the Error
code field) *does* answer, because the code is unique to that problem. It is
the vaguer IT questions that decline, not the precise ones.

---

## Two things not to demo

- **`compliance`, `hr_systems`, `sap_addons` records.** These are filtered out
  at ingestion on purpose — one is marked junk, one is access-restricted, one
  is still `Escalated` with no proven fix. The engine correctly declines,
  but it is not a retrieval failure worth showing to a judge.
- **A number from the "Why this" panel.** The default view is plain English
  reasons. The weighted numbers sit behind **Show scoring detail**; open that
  only if someone technical asks how it is scored.

## Difference from Chat, if asked

Chat decides *how to talk* to you — it asks when it is unsure, remembers what
you ruled out, and narrates the choice. Find decides *what is true* — it
matches structured facts, shows the evidence, and refuses when the facts do
not line up. They share one ranking path, so they never contradict each
other: the same query returns the same record on both pages.
