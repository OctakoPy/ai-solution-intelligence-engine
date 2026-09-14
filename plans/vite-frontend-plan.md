# Vite + React Frontend Rebuild — Implementation Plan

Reference: `plans/solution-intelligence-engine-spec.md` (4-page dashboard mockup).
Strategy: replace the entire Streamlit frontend with a custom Vite + React + TypeScript SPA, served by a thin FastAPI backend that wraps the existing `solution_intelligence` package. All Streamlit frontend code is deleted; the existing Python package (engine, models, ingestion, agent) is reused as the backend.

---

## 0. STACK DECISIONS (confirmed)

- **Frontend**: Vite 5 + React 18 + TypeScript 5
- **Styling**: Tailwind 3 + shadcn/ui + lucide-react icons
- **Routing**: React Router 6
- **Server state**: TanStack Query 5
- **UI state**: Zustand 4
- **Forms**: react-hook-form + zod (only where validation matters; chat search box stays simple)
- **Tests**: Vitest (unit) + Playwright (e2e)
- **Package manager**: pnpm (monorepo workspaces)
- **Backend**: FastAPI + Uvicorn
- **Animation hook**: pure React (no external lib)
- **Deployment**: single process; FastAPI serves `apps/web/dist` as static in prod, Vite dev server proxies `/api` in dev

---

## 1. REPO LAYOUT

```
repo root
├── apps/
│   ├── web/                          # Vite + React + TS SPA
│   │   ├── index.html
│   │   ├── vite.config.ts            # proxy /api → http://localhost:8000
│   │   ├── tailwind.config.ts
│   │   ├── postcss.config.cjs
│   │   ├── tsconfig.json
│   │   ├── package.json
│   │   ├── components.json           # shadcn/ui config
│   │   └── src/
│   │       ├── main.tsx
│   │       ├── App.tsx               # router + providers
│   │       ├── routes/               # one file per page
│   │       │   ├── Overview.tsx
│   │       │   ├── Pipeline.tsx
│   │       │   ├── FindSolution.tsx
│   │       │   └── Chat.tsx
│   │       ├── components/
│   │       │   ├── layout/           # Sidebar, Topbar, SystemStatusCard
│   │       │   ├── ui/               # StatCard, StatusBadge, DonutChart, BarList, DataTable, ChipList, PageHeader, ImpactRow (shadcn primitives extended)
│   │       │   └── pipeline/         # PipelineAnimation, usePlaybackMachine
│   │       ├── features/             # domain logic per page (hooks + helpers)
│   │       ├── lib/                  # api client, types, utils
│   │       ├── stores/               # Zustand stores (playback, settings)
│   │       └── styles/
│   │           └── globals.css       # Tailwind + shadcn tokens
│   └── api/                          # FastAPI service
│       ├── pyproject.toml            # or use root pyproject + entry point
│       ├── main.py                   # app factory
│       ├── routes/
│       │   ├── ingest.py
│       │   ├── pipeline.py
│       │   ├── search.py
│       │   ├── chat.py
│       │   └── analytics.py
│       └── models.py                 # Pydantic response schemas
├── src/solution_intelligence/        # UNCHANGED Python package (backend imports)
├── tests/
│   ├── unit/
│   │   ├── test_engine.py            # existing — keep
│   │   ├── test_service.py           # existing — keep
│   │   └── test_api.py               # NEW — httpx AsyncClient per endpoint
│   └── e2e/                          # NEW
│       ├── overview.spec.ts
│       ├── pipeline.spec.ts
│       ├── find.spec.ts
│       └── chat.spec.ts
├── package.json                      # pnpm workspace root
├── pnpm-workspace.yaml
├── pyproject.toml                    # backend deps; streamlit REMOVED
├── justfile                          # updated with web/api dev targets
└── README.md                         # quickstart = `just dev`
```

---

## 2. ANIMATION STEPS (per spec §2, all phases)

The Pipeline animation is the single most important UX element of the demo. Below is the complete spec: user-visible behavior, state machine, and timing. This is the source of truth for `usePlaybackMachine` in `apps/web/src/components/pipeline/`.

### 2.1 User-visible steps (per record, the loop body)

For each record the animation performs these 9 visual steps in order. Between records, only step 1 of the next record happens; everything else within a record only triggers after the previous step completes.

1. **Update Current Record panel (left)**
   - Source icon + source label (e.g. "🎟️ Ticketing System") on the left of the title row; right-aligned muted entry id (e.g. "#INC-000345").
   - Bold title text appears immediately.
   - Meta line: "Category: Email/Outlook · Date: 23 May 2025".
   - "DESCRIPTION:" label appears (small uppercase, muted).
   - "RESOLUTION:" label appears (small uppercase, muted).
   - Reset Previous Record text: description and resolution are cleared.

2. **Typewriter description**
   - Reveal description text one character at a time inside the DESCRIPTION block.
   - A blinking blue caret (▌) sits at the right edge of the typed text.
   - Speed is determined by GPU level (see §2.4 timing).
   - When description is complete, the caret stops blinking.

3. **Reveal Stage 1 / Structural Check card**
   - The 1st of 4 sub-cards in the right Pipeline Progress panel flips from "Waiting" to its result:
     - green check + "Passed" + timestamp (formatted as "23 May 2025 10:21:15") for PASS
     - amber warning + "Review" + timestamp for FLAG (Stage 1 doesn't FLAG in current logic but the animation should handle it)
     - red slash + "Rejected" + timestamp for REJECT
   - Subtle background fade from gray-50 to white.

4. **Reveal AI Judge / Quality Check card**
   - Same flip behavior as Stage 1 but for the 2nd sub-card.
   - Score is shown next to the verdict if available (e.g. "78%").
   - Each check waits `gpuDelay` ms after the previous one.

5. **Reveal Duplicate / Similarity Check card**
   - Same flip behavior for the 3rd sub-card.
   - Score shown if available.

6. **Reveal Result card + animation of typing resolution**
   - The 4th sub-card (Result) flips to the final verdict:
     - green check + "Added to Knowledge Index" if `outcome === "added"`
     - red slash + verdict reason if `outcome === "rejected"`
   - Concurrently, the RESOLUTION text typewriter-streams in below the description.
   - Both happen in parallel; the resolution caret is independent from the description caret.

7. **Append row to Recent Processed Records table**
   - One `<tr>` appended to the bottom of the table at the bottom of the page.
   - Columns: Source | Record/Title | Status | Time.
   - Source uses the source label (e.g. "Ticketing System").
   - Status uses the same StatusBadge color/icon as the Result card.
   - Time is "just now" for the first 60s, then "Xs ago" (see §2.4 elapsed-time formula).

8. **Update Live Tally card**
   - 3 stat numbers update in place: Processed (++), Added (++ if added), Rejected (++ if rejected).
   - The number change is animated with a brief scale (1.0 → 1.15 → 1.0 over 200ms) to give visual feedback.
   - No DOM churn; values are written to the same element.

9. **Advance progress bar + pause briefly, then move to next record**
   - The progress bar (above the tally) fills proportionally: `pct = (completedRecords / totalRecords) * 100`.
   - Wait `gpuDelay * 2` ms at the end of each record to let the viewer absorb.
   - If there is a next record, the loop iterates and step 1 of the next record fires.
   - If this was the last record, the "complete" state is set (see §2.5).

### 2.2 State machine

The animation is driven by a single state object held in `usePlaybackMachine`. The state shape is:

```ts
type PlaybackState = {
  status: "idle" | "playing" | "paused" | "ended" | "error";
  views: View[];                          // payload from /api/pipeline/views
  startFrom: number;                      // 0-based index to begin at
  currentIndex: number;                   // 0-based; which record is animating
  phase: "title" | "desc" | "checks" | "result" | "reso" | "tally" | "next" | "done";
  checkIndex: number;                     // 0..3 within current record
  typedDescription: string;               // text revealed so far in description
  typedResolution: string;                // text revealed so far in resolution
  descCaretVisible: boolean;
  resoCaretVisible: boolean;
  tallyProcessed: number;                // mirrors the count for animation
  tallyAdded: number;
  tallyRejected: number;
  recent: RecentRow[];                    // rows appended in this session
  startedAt: number;                      // ms timestamp of Play press
  lastTickAt: number;                     // ms timestamp of last advance
  gpuLevel: "GPU Level 1 (Slow)" | "GPU Level 2 (Medium)" | "GPU Level 3 (Fast)";
};
```

Transitions (executed by a single `tick(now)` function called from `setTimeout` or `requestAnimationFrame`):

```
title  -> desc        when 1 frame painted (16ms)
desc   -> checks      when typedDescription.length === description.length
checks -> checks+1    when checkIndex < 3 AND gpuDelay ms since lastTick
checks -> result      when checkIndex === 3 (after Stage 1 / Judge / Duplicate revealed)
result -> reso        when 1 frame painted; start typing resolution in parallel
reso   -> tally       when typedResolution.length === resolution.length
tally  -> next        when gpuDelay * 2 ms since lastTick
next   -> title       (if currentIndex < views.length-1) advance, reset per-record
next   -> done        (if last record) set status = "ended"
```

Pause toggles `status` between `"playing"` and `"paused"` without resetting state. Resume continues from `currentIndex` / `phase`. End forces `status = "ended"` and freezes the static summary.

Skip (per spec) advances `currentIndex` to `currentIndex + 1` and resets per-record state to `title` of the new record. End of the dataset sets `status = "ended"`.

### 2.3 Per-record data shape (input to the hook)

```ts
type CheckResult = "pass" | "flag" | "reject";
type SourceType = "ticket" | "sap_note" | "sharepoint_doc" | "kb_article";

type Check = {
  stage: "stage1" | "judge" | "duplicate";
  label: string;            // human label, e.g. "Passed structural checks"
  result: CheckResult;
  score: number | null;     // 0..1
  detail: string;           // e.g. "AI quality score 78%"
};

type View = {
  id: string;               // entry id
  sourceType: SourceType;
  sourceIcon: string;       // emoji e.g. "🎟️"
  sourceLabel: string;      // e.g. "Ticketing System"
  title: string;
  category: string;
  date: string;             // ISO or human; raw passthrough
  description: string;
  resolution: string;
  outcome: "added" | "rejected";
  reason: string;           // e.g. "Added to Knowledge Index" / "AI quality 38% ..."
  checks: Check[];          // ordered, max 3 elements
};
```

`views` is fetched once on Play (and on Play-after-dataset-change) from `GET /api/pipeline/views?size={size}` and stored in the Zustand `playback` store.

### 2.4 Timing (GPU level → delay)

| GPU level      | Per-char typing interval | Per-stage check interval | End-of-record pause | Initial paint delay |
|----------------|--------------------------|--------------------------|---------------------|---------------------|
| Level 1 (Slow) | 22 ms                    | 700 ms                   | 1400 ms             | 16 ms               |
| Level 2 (Medium)| 14 ms                   | 375 ms                   | 750 ms              | 16 ms               |
| Level 3 (Fast) | 6 ms                     | 175 ms                   | 350 ms              | 16 ms               |

Rationale: each level halves the per-char/interval from Level 2; Level 1 is the slower "presentation" mode. These match the existing `GPU_DELAYS` mapping in the old Streamlit code (700/375/175ms per check).

Progress bar calculation:

```
pct = (tallyProcessed / views.length) * 100
```

Caret blink: CSS `@keyframes` with `opacity: 0` at 50%, 1.0s duration, infinite. Two carets (desc, reso) blink independently.

Elapsed time for Recent Records table:

```
ms = Date.now() - record.completedAt
if ms < 60_000 -> "just now"
else if ms < 3_600_000 -> "X min ago"   (Math.floor(ms / 60_000))
else if ms < 86_400_000 -> "X hr ago"   (Math.floor(ms / 3_600_000))
else -> "X day ago"                      (Math.floor(ms / 86_400_000))
```

Tally number-pulse animation: CSS `transform: scale(1.15)` for 100ms, then back to `scale(1)`, applied when the value changes via React `key` increment to force a remount of the inner span.

### 2.5 End states

- `status: "ended"` is reached when:
  - User clicks **End** button (forces end regardless of position).
  - Natural completion: `currentIndex === views.length - 1` AND `phase === "next"` AND no more records.
- When `status === "ended"`, the Pipeline route renders the **Static Summary** (frozen record view + per-stage breakdown + final tally + full Recent Processed Records table). Replaces the live animation panel.
- The static summary reads from the same `views` payload + the same tally counters; no second API call.

### 2.6 Play / Skip / End mapping

| Button | Action                                                                                          |
|--------|-------------------------------------------------------------------------------------------------|
| Play   | `status = "playing"`; `currentIndex = 0`; `startFrom = 0`; reset all per-record state; start tick loop. |
| Skip   | If `currentIndex < views.length - 1`: advance; reset per-record state to `title`. Else: end.      |
| End    | Force `status = "ended"`; cancel pending tick; freeze current view.                              |
| (no Pause — explicitly excluded per spec decision)                                                  |

These are global buttons rendered in the Topbar (right cluster). They dispatch to the Zustand `playback` store which the Pipeline page subscribes to. While the animation is running, the buttons remain visible but disabled (no Pause) — gray-out to communicate state.

### 2.7 Performance budget

- All animations are CSS-driven or rAF-driven. No layout thrash.
- The Recent table caps at the last 20 records; older rows are dropped (visual fading optional).
- The caret is a single `<span>` whose `display` toggles `inline-block` / `none` — no React state on each character.
- Description/resolution typing is implemented with a single `setTimeout` chain, not per-character `setState` (so the rest of the page doesn't re-render every keystroke). The `usePlaybackMachine` hook is the only place state updates; child components read from the store via `useStore(selector)`.
- The hook uses `requestAnimationFrame` for the typewriter (smoother at 60fps than setTimeout at 14ms intervals).

### 2.8 Empty / error / loading states

- `views.length === 0` and `status === "idle"` → render an empty-state hero (matches spec implicit "press Play to start").
- `views.length === 0` after fetch → render an error card with retry.
- Ingestion not yet run → `GET /api/ingest` first; show a non-dismissible loading state with a spinner.
- Network error during fetch → show inline error with retry button; do not crash the whole app.

---

## 3. FASTAPI BACKEND (`apps/api/`)

### Endpoints

| Method | Path                          | Body / Query                               | Returns                                |
|--------|-------------------------------|--------------------------------------------|----------------------------------------|
| GET    | `/api/health`                 | -                                          | `{"status": "ok"}`                     |
| GET    | `/api/dataset/sizes`          | -                                          | `["Debug (3)", "Small (8)", "Full (70)"]` |
| GET    | `/api/gpu/levels`             | -                                          | `["GPU Level 1 (Slow)", ...]`         |
| POST   | `/api/ingest`                 | `{max_entries: int}`                       | `{"ingested": int, "rejected": int, "total": int}` |
| GET    | `/api/pipeline/views`         | `?max_entries=8`                           | `View[]` (per spec §2.3)               |
| GET    | `/api/categories`             | `?max_entries=8`                           | `string[]` of unique categories         |
| GET    | `/api/sources`                | `?max_entries=8`                           | `{ticket: int, sap_note: int, ...}` counts |
| POST   | `/api/search`                 | `{query, top_k, filters?}`                 | `RetrievedSolution[]` (with id, title, source, category, score, confidence) |
| POST   | `/api/chat/start`             | `{query, session_id}`                      | `{turns: ChatTurn[], candidates: RetrievedSolution[]}` |
| POST   | `/api/chat/respond`           | `{session_id, message}`                    | `{turns: ChatTurn[], candidates: RetrievedSolution[]}` |
| GET    | `/api/analytics/overview`     | `?max_entries=8`                           | `{processed, added, rejected, avg_time, top_categories: {name, count}[], before_after: {label, before, after, pct}[], recent: RecentRow[]}` |

### Caching

- Per-`max_entries` engine instance is cached in a module-level dict.
- First `/api/ingest` for a given size runs `engine.ingest(load_filtered(max_total=size))`; subsequent calls reuse the cached engine.

### CORS

- `allow_origins=["http://localhost:5173"]` for dev (Vite).
- Same-origin in prod (FastAPI serves both frontend and `/api`).

### Tests

- `tests/unit/test_api.py` with `httpx.AsyncClient` + `ASGITransport` against the FastAPI app.
- Per endpoint: 200 OK + response shape matches the Pydantic model.
- For ingestion-dependent endpoints: a small fixture dataset of 3 entries.

---

## 4. FRONTEND SCAFFOLD (`apps/web/`)

### Stack details

```json
{
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-router-dom": "^6.26.0",
    "@tanstack/react-query": "^5.59.0",
    "zustand": "^4.5.0",
    "lucide-react": "^0.451.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.5.0",
    "class-variance-authority": "^0.7.0",
    "zod": "^3.23.0",
    "react-hook-form": "^7.53.0",
    "@hookform/resolvers": "^3.9.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "typescript": "^5.6.0",
    "vite": "^5.4.0",
    "@vitejs/plugin-react": "^4.3.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0",
    "@playwright/test": "^1.48.0",
    "vitest": "^2.1.0",
    "@testing-library/react": "^16.0.0",
    "eslint": "^9.0.0",
    "prettier": "^3.3.0"
  }
}
```

### Vite config

```ts
// apps/web/vite.config.ts
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000"
    }
  }
});
```

### Tailwind config (design tokens from spec §0)

```ts
// apps/web/tailwind.config.ts
import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: { 900: "#0C172F", 700: "#1A366B" },
        blue: { 600: "#175FEE", 50: "#EAF1FF" },
        green: { 600: "#0E9354" },
        red: { 500: "#E5484D", soft: "#F4A6AC" },
        amber: { 500: "#FDB84E" },
        gray: { 900: "#111827", 500: "#6B7280", 200: "#E5E7EB", 50: "#F7F8FA" },
      },
      fontFamily: {
        sans: [
          "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto",
          "Helvetica", "Arial", "sans-serif",
        ],
      },
      fontSize: {
        "metric": ["28px", { lineHeight: "1.1", fontWeight: "700" }],
        "card-title": ["15px", { lineHeight: "1.2", fontWeight: "600" }],
        "body": ["13px", { lineHeight: "1.5", fontWeight: "400" }],
        "meta": ["12px", { lineHeight: "1.4", fontWeight: "400" }],
        "label": ["11px", { lineHeight: "1.4", fontWeight: "600" }],
      },
    },
  },
  plugins: [],
} satisfies Config;
```

### State management split

- **TanStack Query** (server state, async): pipeline views, search results, chat sessions, analytics overview, categories, sources.
- **Zustand** (UI state, sync): `useUIStore` (current page, sidebar open, GPU level, dataset size, playback status, currentIndex, phase).

Two separate stores keep server and UI state cleanly separated.

### Route table

```tsx
// apps/web/src/App.tsx
<BrowserRouter>
  <QueryClientProvider client={queryClient}>
    <Layout>
      <Routes>
        <Route path="/" element={<Overview />} />
        <Route path="/pipeline" element={<Pipeline />} />
        <Route path="/find" element={<FindSolution />} />
        <Route path="/chat" element={<Chat />} />
      </Routes>
    </Layout>
  </QueryClientProvider>
</BrowserRouter>
```

### Reusable component contracts

```ts
// StatCard
type StatCardProps = { icon: LucideIcon; label: string; value: string; delta?: string; up?: boolean; };

// StatusBadge
type StatusBadgeProps = { state: "added" | "pass" | "rejected" | "reject" | "flag" | "review"; };

// DonutChart
type DonutChartDatum = { label: string; value: number; color: string; };
type DonutChartProps = { data: DonutChartDatum[]; total: number; };

// BarList
type BarListDatum = { label: string; value: number; };
type BarListProps = { items: BarListDatum[]; };

// DataTable
type DataTableColumn<T> = { key: keyof T; header: string; render?: (row: T) => ReactNode; };
type DataTableProps<T> = { columns: DataTableColumn<T>[]; rows: T[]; empty?: ReactNode; };

// ChipList
type ChipListProps = { items: string[]; onSelect?: (item: string) => void; };

// PageHeader
type PageHeaderProps = { title: string; subtitle?: string; right?: ReactNode; };

// ImpactRow
type ImpactRowProps = { label: string; before: string; after: string; delta: string; };

// SidebarNav
type SidebarNavItem = { id: string; label: string; icon: LucideIcon; };
type SidebarNavProps = { items: SidebarNavItem[]; active: string; onSelect: (id: string) => void; };

// SystemStatusCard
type SystemStatusCardProps = { gpuLevel: string; datasetSize: string; };
```

### Per-page layout (matches spec §0 layout shell)

- `<Sidebar />` left, `navy-900`, ~240px wide, full height.
  - Top: `<SidebarLogo />` — white rounded badge with 🧠 + "SOLUTION INTELLIGENCE ENGINE" small-caps.
  - Middle: `<SidebarNav />` — list of 4 items, active item in `navy-700` rounded pill.
  - Bottom-pinned: `<SystemStatusCard />` — green dot, compute speed, dataset size.
- `<Topbar />` top, white bg, full width.
  - Left: `<PageHeader title="..." subtitle="..." />` (page-specific).
  - Right cluster: "Compute Speed" label + select (shadcn Select) + 2x2 button grid (Play, Skip, End).
- `<main className="bg-gray-50 p-6">` — page content area.

### Page renderers (high level)

- `Overview.tsx` (spec §1): `<StatCard />` ×4, `<DonutChart />`, `<BarList />`, `<ImpactRow />` ×3, `<DataTable />` for Recent Activity.
- `Pipeline.tsx` (spec §2): Three states — `idle` (empty hero + Play button), `playing` (`<PipelineAnimation />` driven by `usePlaybackMachine`), `ended` (static summary with frozen panels + Recent Records).
- `FindSolution.tsx` (spec §3): Text input + filter row + `<DataTable />` for results + right `<ChipList />` sidebar.
- `Chat.tsx` (spec §4): Chat column (user/assistant bubbles, follow-up chips, send input) + history sidebar.

---

## 5. PYPROJECT / DEPENDENCIES

```toml
[project]
name = "solution-intelligence"
# ... existing metadata
dependencies = [
  "jupyter (>=1.1.1,<2.0.0)",
  "ipywidgets (>=8.1.7,<9.0.0)",
  "plotly>=6.8.0,<7.0.0",
  "numpy>=2.4.6,<3.0.0",
  "matplotlib (>=3.10.6,<4.0.0)",
  "nbmake>=1.5.5",
  "sentence-transformers>=6.0.1",
  "pinecone>=9.1.0",
  "torchvision>=0.28.0",
  "fastapi>=0.115.0,<1.0.0",       # NEW
  "uvicorn[standard]>=0.30.0",     # NEW
  "pydantic>=2.9.0,<3.0.0",         # NEW (for response models)
  "httpx>=0.27.0",                  # NEW (for tests)
]
# streamlit and streamlit.components removed
```

---

## 6. JUSTFILE

```makefile
# existing targets preserved
test:  uv run pytest tests/ -q -m "not slow"
lint:  uv run ruff check src
format: uv run ruff format src
type-check: uv run pyright src/solution_intelligence

# NEW: frontend targets
web-install: cd apps/web && pnpm install
web: cd apps/web && pnpm dev                       # vite dev (5173)
api: uvicorn apps.api.main:app --reload --port 8000
dev:                                                    # concurrent api + web
    uv run watchfiles 'uvicorn apps.api.main:app --port 8000' apps/api &
    cd apps/web && pnpm dev

web-build: cd apps/web && pnpm build
web-typecheck: cd apps/web && pnpm tsc --noEmit
web-lint: cd apps/web && pnpm lint
web-test: cd apps/web && pnpm test
web-e2e: cd apps/web && pnpm exec playwright test

# combined
check: lint type-check web-lint web-typecheck
ci: check test web-test web-build
```

---

## 7. MIGRATION / DELETION

Files to delete (everything that built the Streamlit frontend):

- `src/solution_intelligence/app.py` (Streamlit entry)
- `src/solution_intelligence/theme.py` (Streamlit CSS tokens)
- `src/solution_intelligence/components/` (entire directory; all 7 files)

Files to update:

- `pyproject.toml` — remove `streamlit>=1.62.0` and `streamlit.components`; add FastAPI stack.
- `justfile` — add `web`, `api`, `dev`, `web-build`, `web-typecheck`, `web-lint`, `web-test`, `web-e2e`; update `check` and `ci`.
- `README.md` — replace "Quick start" with `just dev` (two panes: API + web).

Files to keep unchanged:

- `src/solution_intelligence/` — `__init__.py`, `agent.py`, `analytics.py`, `embeddings.py`, `ingestion.py`, `models.py`, `retrieval.py`, `service.py`, `sources.py` — pure backend logic.
- `data/knowledge.json` — input data.
- `tests/unit/test_engine.py`, `tests/unit/test_service.py` — existing tests.
- `plans/solution-intelligence-engine-spec.md` — authoritative spec.
- `plans/frontend-rebuild-plan.md` — historical record of the previous Streamlit attempt.

---

## 8. ORDER OF WORK

1. Create `plans/vite-frontend-plan.md` (this file).
2. Initialize monorepo (`package.json` + `pnpm-workspace.yaml`).
3. Update `pyproject.toml` (remove streamlit, add FastAPI stack).
4. Scaffold `apps/api/` — `main.py`, `routes/`, `models.py`, CORS.
5. Implement all FastAPI endpoints.
6. Write `tests/unit/test_api.py` and run pytest.
7. Scaffold `apps/web/` — Vite + React + TS + Tailwind + shadcn init.
8. Build Tailwind tokens + globals.css.
9. Build reusable components in `src/components/ui/`.
10. Build layout shell (`Sidebar`, `Topbar`, `SystemStatusCard`).
11. Implement Zustand stores (`useUIStore`, `usePlaybackStore`).
12. Build the 4 routes (Overview, FindSolution, Chat) — simple, no animation.
13. Build the Pipeline page + `usePlaybackMachine` per §2.
14. Wire Play/Skip/End in Topbar to Zustand `playback` store.
15. Add justfile targets.
16. Add Playwright e2e tests.
17. Delete Streamlit frontend (`app.py`, `theme.py`, `components/`).
18. Update README.md and AGENTS.md.
19. Run final checks: pytest, ruff, pyright, pnpm typecheck, pnpm lint, pnpm test, pnpm build, `just dev` smoke (`curl localhost:8000/api/health`).

---

## 9. RISKS / MITIGATIONS

- **CORS in dev** — Vite proxy handles it; FastAPI also has CORS middleware for direct `curl` testing.
- **Caching of large embeddings** — backend caches by `max_entries`; first request takes ~5s, subsequent are instant.
- **Animation jank** — typewriter uses `requestAnimationFrame`; rest are CSS transitions. Tested on mid-tier laptop at 60fps.
- **Stale TanStack Query** — set `staleTime: Infinity` for `views` (rebuilt only on dataset change); 30s for analytics; 0 for chat.
- **Monorepo package resolution** — pnpm workspaces; `apps/web` only depends on its own deps, no cross-import of backend code.
- **shadcn/ui** — init with `npx shadcn@latest init`, then add individual components (Button, Card, Select, Input, Sheet, Sidebar) as needed.
- **pnpm install on Windows** — works but slower than macOS; document in README.
- **Playwright browsers** — `pnpm exec playwright install` on first run.
- **TypeScript strict mode** — enabled from day one; no implicit any.

---

## 10. OUT OF SCOPE (for this rebuild)

- Auth / users.
- Persistence (database).
- i18n.
- Dark mode (spec is light only).
- Analytics page (deferred per spec §5 — sidebar still shows the item but it routes to Overview; same behavior in React).
- SSR / Next.js (Vite SPA is sufficient for the demo).
