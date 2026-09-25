# Find a Solution — the demo, step by step

Everything you need on one page. Type the query exactly as written, fill the
fields exactly as written, and you will get exactly what is described.

All values below were measured from the running system, not estimated.

**Before you start:** `just dev` → dataset **Full (78)**. Hard-refresh the
browser (Ctrl+R) so the dashboard is current.

---

## Beat 1 — The context trap ★ best beat, do this one

This is the clearest answer to *"why not just use Google?"*

### Step 1a — search with no detail

**Type in the search box:**

```
goods receipt posting error account determination not found
```

Click **Search**. Leave the Incident details panel closed.

**You see:** `TIC-3011` first, with no badges, and the line *"High confidence
— this fix has worked every time it was tried"* plus **worked 6 of 6**.

> Say: *"It found the right problem from the description alone, but it has no
> way to know which environment you're actually in."*

### Step 1b — add the detail

Click **Incident details (optional)** to expand it. Fill in all three:

| Field | Type this |
| --- | --- |
| Error code | `M8149` |
| System / module | `SAP MM` |
| Environment | `PROD` |

The line under the panel reads *"Searching with: error M8149 · SAP MM · PROD"*.
Click **Search**.

**You see:** `TIC-3011` is still first, now with **three green badges** —
Error code match, System / module match, Environment match.

> Say: *"Now it isn't guessing from wording — all three facts line up."*

### Step 1c — change one thing

In the **Environment** box, replace `PROD` with `UAT`. Click **Search**.

**You see:** the order flips.

| Position | Record | Badges |
| --- | --- | --- |
| **1st** | `TIC-3012` — *M8149 goods receipt posting error in **UAT** sandbox* | Error code ✓ System ✓ **Environment ✓** |
| 2nd | `TIC-3011` — the PROD record | Error code ✓ System ✓ **Environment ✗** |

**Expand the 2nd card** (`TIC-3011`) and it carries an amber warning:

> *Verify root cause before applying: this record matches part of your
> incident context but conflicts on environment — evidence may be from a
> different context.*

> Say: *"Same error code, same system, different environment — and a different
> root cause. A keyword search cannot tell these apart."*

**Then change the Environment back to `PROD` and search again** so the demo
ends in a clean state. `TIC-3011` returns to first place.

---

## Beat 2 — Multilingual, one query, three languages

**Type:**

```
user cannot access financial reports in sap, authorization error
```

No incident details. Click **Search**.

**You see five cards**, and three of them are the same fix:

| # | Record | Language badge |
| --- | --- | --- |
| 1 | User cannot access FI reports in SAP - authorization error | — (English) |
| 2 | SAP authorization error when accessing controlling reports | — (English) |
| 3 | SAP Note: SU53 authorization trace usage | — (English) |
| 4 | 用户无法访问SAP中的FI财务报告 | **中文** |
| 5 | Pengguna tidak boleh buka laporan FI dalam SAP | **BM** |

**Click "View" on the Chinese card**, then click **Translate to English**.

The whole entry flips — title, description, and resolution — to:

> *User cannot access FI financial reports in SAP*
> *Checked role assignment in SU01. User was missing the Z_FI_REPORT_DISPLAY
> role…*

> Say: *"One English question, answered in three languages — and the
> translation is stored, not machine-guessed at read time."*

**Two more that work the same way** (use if you want a second example):

| Type this | You get |
| --- | --- |
| `vpn keeps dropping and will not reconnect` | English + **BM** + **中文** |
| `user locked out of account cannot log in` | English + **中文** + **BM** |

---

## Beat 3 — It refuses when it should

**Type:**

```
the quarterly compliance export custom ABAP program keeps erroring
```

**You see:** an amber banner and *"Nothing in the knowledge base matches this
closely enough to recommend. Escalate to a subject-matter expert rather than
applying a guess."*

> Say: *"That sounds exactly like a real ticket, and the honest answer is that
> we have never seen it. Better to escalate than to invent a fix."*

Also verified if you need a second: `i ran out of milk in my house`.

---

## Fillers — if you need a few seconds on screen

| Type this | You get |
| --- | --- |
| `user cannot access FI reports in SAP, authorization error` | The 8 of 8 authorization fix |
| `VPN drops after 5 minutes, reconnect fails on Windows 11` | VPN fix, 11 of 13 |
| `the nightly sap batch job for inventory reconciliation keeps short dumping` | Batch job, 6 of 7 |
| `cannot open excel attachment from sap workflow inbox` | Workflow attachment, 11 of 11 |
| `SAP transaction ME23N running slow for Finance team` | Performance fix, 7 of 7 |

---

## What to click, and what it shows

| Click | Shows |
| --- | --- |
| **View Details** | Description, full resolution, and the **Why this** panel |
| **Why this** panel | Plain-English reasons: *"The error code you gave matches this record exactly"*, *"It has worked every time it was tried"* |
| **Show scoring detail** | The weighted numbers behind the score, labelled *"These are not probabilities"* — only if someone technical asks |
| **Yes / No** under *Did this work?* | Records the outcome and changes future results |

**Do not** quote a percentage from the card. The confidence number is a
weighted blend, not a probability, and it is not shown by default for that
reason. Quote the **track record** instead — "worked 8 of 8" is concrete and
cannot be misread.

---

## Reset between rehearsals

Restart the API (`just dev`, or stop and start it). Every outcome you click
during a rehearsal is wiped and the seeded state returns, so a practice run
never damages the real demo. The Overview page confirms it: 14 outcomes, 11
worked, 3 rejected.

---

## Do not demo these

- **`compliance`, `hr_systems`, `sap_addons` records** — filtered out at
  ingestion on purpose (junk, access-restricted, and unresolved
  respectively). The engine correctly declines, but it is not worth showing.
- **Any percentage** — see above.
- **The scoring detail panel** — unless someone asks how the ranking works.
