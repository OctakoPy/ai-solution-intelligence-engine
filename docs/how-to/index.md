# How-To

Practical recipes for working with the Solution Intelligence Engine.

## Run everything with `just`

```bash
just dev                # API (:8004) + web (:5179) concurrently
```

Both processes are started concurrently and stop with Ctrl+C.

## Run the API or the frontend alone

```bash
just api                # FastAPI only, http://localhost:8004/docs
just web                # Vite dev server only, http://localhost:5179
```

The Vite dev server proxies `/api` to `:8004`, so the dashboard works without
extra configuration. Without `just`, run the underlying commands from the
`justfile` at the repository root.

## Use the engine from Python

```python
from solution_intelligence.service import SolutionEngine
from solution_intelligence.sources import load_filtered

engine = SolutionEngine()
engine.ingest(load_filtered(max_total=12))

for hit in engine.search("SAP FI report access denied authorization error", top_k=3):
    print(hit.entry.title, f"{hit.combined_score:.0%}")
```

## Run the dataset sizes locally

The dashboard exposes a dataset-size selector (Debug 3 / Small 8 / Full 78)
backed by the API. To re-process a different slice, restart the API after
changing the selector, or pass a size directly:

```bash
curl -X POST http://localhost:8004/api/ingest -H "Content-Type: application/json" -d '{"max_entries": 78}'
```

## Run the pilot evaluation

The eval framework measures whether outcome-aware ranking actually helps,
using a labeled query -> expected-solution set built from the demo dataset:

```bash
just eval
# or, with a dataset cap:
uv run python scripts/run_eval.py --max-entries 78
```

It compares three ranking modes on the same cases:

| Mode | What it measures |
| --- | --- |
| `similarity` | Raw similarity ranking (the pre-outcome-aware baseline) |
| `no_context` | Outcome-aware confidence, structured incident context dropped |
| `context` | The shipped behavior: confidence ranking + incident context |

Metrics per mode: top-1 and top-3 success rate, mean reciprocal rank,
confidence on hits vs misses (calibration), abstain precision on the
honest-gap cases, and whether the M8149 UAT context trap is resisted. A
machine-readable summary is written to `data/eval_report.json` (gitignored;
reproduce it any time with `just eval`).

## Add tests

Backend tests live in `tests/unit/` and run with pytest through uv:

```bash
uv run pytest -q tests/unit/test_api.py
```

Frontend unit tests live next to the source under `apps/web/src/**` and run
with Vitest:

```bash
just web-test
```

End-to-end tests use Playwright (`.spec.ts` under `apps/web/tests/e2e/`):

```bash
just web-e2e
```
