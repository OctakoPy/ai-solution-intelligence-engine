# Tutorials

Start here to see what the Solution Intelligence Engine can do with the demo
dataset (76 records across tickets, SAP notes, SharePoint documents, and
knowledge-base articles).

## Quick start

1. **Install** — `uv sync --all-groups` and `npm install`.
2. **Run** — `just dev` (FastAPI on `:8004`, Vite on `:5179`).
3. **Open** — <http://localhost:5179> and follow the dashboard order below.

## Dashboard tour

The app has four pages, best demonstrated in this order:

- **Overview** — KPIs on the processed day: added / flagged / rejected counts,
  average processing time, flagged-for-review queue, and resolution time by
  category.
- **Pipeline** — a live animation of records flowing through the three-stage
  gauntlet (Stage 1 structural check → AI quality judge → duplicate check)
  with per-ticket verdicts.
- **Find a Solution** — semantic search with per-result confidence, source,
  similarity breakdown, and an expandable step-by-step resolution.
- **Chat** — conversational refinement: follow-up questions re-rank candidates
  against the same trusted index.

You can read and try example queries in the guided
[demo script](demo-script.md).

## What to look for

- **Trust-first answers** — every result shows *why*: source system,
  similarity, confidence, and historical success rate.
- **Honest gap handling** — novel issues that aren't in the knowledge base get
  a low-confidence "escalate to a human" answer, never a fabricated fix.
- **Trilingual retrieval** — one English query surfaces English, Bahasa
  Malaysia, and Chinese versions of a matching solution (expand a non-English
  result and hit **Translate to English**).
