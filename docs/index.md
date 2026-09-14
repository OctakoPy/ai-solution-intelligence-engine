# Welcome to Solution Intelligence Engine!

An AI-powered enterprise knowledge engine that ingests records from tickets,
SAP, SharePoint, and knowledge-base systems, grades them for quality, catches
near-duplicates, and surfaces **proven** solutions — with a transparent
"why" panel and trilingual (English / Bahasa Malaysia / Chinese) retrieval.

![Solution Intelligence Engine dashboard](assets/overview.png)

## Start here

- **Try it** — the [demo script](tutorials/demo-script.md) walks through 76
  demo records query by query.
- **Use it** — set up and run the engine in the [how-to guide](how-to/index.md).
- **Understand it** — see the reasoning behind confidence scores, duplicate
  checks, and human-in-the-loop review in the [explanation](explanation/index.md).
- **Read the code** — every module is documented in the [API reference](reference/index.md).

Architectural decisions are recorded in the [ADR section](architecture/adr/index.md).

## What it does differently

- **Trust-first answers** — every result shows *why*: source, similarity,
  confidence, and historical success rate.
- **Transparent pipeline** — accepted / flagged / rejected, with the AI's
  reasoning attached to every judgment call.
- **Honest gap handling** — novel issues earn a low-confidence "escalate to a
  human" answer, never a fabricated fix.