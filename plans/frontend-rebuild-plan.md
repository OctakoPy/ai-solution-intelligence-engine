# Solution Intelligence Engine — Frontend Rebuild Plan

Reference: `plans/solution-intelligence-engine-spec.md` (4-page dashboard mockup spec).
Goal: eradicate the current single-page Streamlit frontend and rebuild it as a
4-page dashboard matching the spec, using Streamlit + custom CSS/HTML.

---

## 0. OVERRIDES & DECISIONS (confirmed with user)

1. **Playback model**: no Pause. Controls are **Play** (start from beginning),
   **Skip record**, **End** (jump to static summary). Playback runs fully via a
   client-side component; `End` renders the static summary immediately.
2. **Analytics page**: deferred. The sidebar still shows the "Analytics" nav item
   but it routes to Overview for now. (User: "Remove analytics for now: maybe later".)
3. **Sections non-animated on Find/Chat/Overview** rendered as normal Streamlit
   widgets (cards/tables/inputs are fine as native Streamlit) — acceptable.
4. **Tech approach**: Streamlit multi-page app (`streamlit/pages`) is rejected —
   instead a **single `app.py` with an internal page state** driven by the
   sidebar nav, because the 4 pages share one header/sidebar/global state (GPU
   level, dataset size, playback). A single entry point keeps hot reload simple.
   The **animation** is delivered as a self-contained HTML string via `st.iframe`
   (replaces the deprecated `st.components.v1.html`) — client-side JS drives the
   timing, avoiding the fragile `st.rerun()` + `time.sleep()` loop.
5. **st.components.v1.html → st.iframe**: confirmed available
   (`st.iframe(src, width="stretch", height="content")` accepts raw HTML strings,
   auto-sizes to content). All legacy `st.components.v1.html` usage is removed.

---

## 1. TARGET ARCHITECTURE

```
src/solution_intelligence/
  app.py                 # single entry point; routes to page renderers
  theme.py               # DESIGN SYSTEM values + CSS builder (old constants.py)
  components/
    __init__.py
    chrome.py            # sidebar + top header shell (shared, all pages)
    playback.py          # Play/Skip/End + playback state, client-side iframe anim
    overview.py          # Page 1 renderer
    pipeline.py          # Page 2 renderer (current record + progress + tally + table)
    solution_finder.py   # Page 3 renderer (search + filters + results + refine)
    chat.py              # Page 4 renderer (chat + history sidebar)
    widgets.py           # reusable: stat card, status badge, donut, bar list,
                         #   table, chips (pure HTML/CSS builders returning str)
  service.py             # UNAFFECTED (backend engine: ingest/search/agent)
  models.py              # UNAFFECTED (core data models)
  ingestion.py           # UNAFFECTED (pipeline)
  agent.py               # UNAFFECTED
```

Old files to remove: `constants.py`, `components/animation_state.py`,
`components/header.py`, `components/playback_controls.py`,
`components/record_view.py`, `components/summary.py`.

`theme.py` replaces `constants.py`: it holds the design tokens (colors, type
scale, spacing) and a `build_css()` returning a `<style>` block injected once
per page.

---

## 2. GLOBAL DESIGN SYSTEM — `theme.py`

- Constants mirroring spec tokens:
  - `NAVY_900 = "#0C172F"`, `NAVY_700 = "#1A366B"`, `BLUE_600 = "#175FEE"`,
    `BLUE_50 = "#EAF1FF"`, `GREEN_600 = "#0E9354"`, `RED_500 = "#E5484D"`,
    `AMBER_500 = "#FDB84E"`, `GRAY_900 = "#111827"`, `GRAY_500 = "#6B7280"`,
    `GRAY_200 = "#E5E7EB"`, `GRAY_50 = "#F7F8FA"`, `WHITE = "#FFFFFF"`.
  - `FONT = "system sans-serif stack"`.
  - Type scale: title 20-22px bold; subtitle 13px; card title 14-15px semibold;
    body 13px; metric 26-28px bold; meta 11-12px; links 12-13px medium.
- `build_css()` -> single `<style>` string applied via
  `st.markdown(css, unsafe_allow_html=True)` at the top of `main()`:
  - Body bg `gray-50`, sidebar `navy-900` (streamlit via `[data-testid="stSidebar"]` layer),
    card class `.si-card` (white bg, 1px gray-200 border, 8-12px radius, shadow),
    `.si-metric` (big number 28px bold + label 12px gray-500 + delta 12px),
    `.si-badge` status colors, `.si-donut`, `.si-bar`, `.si-table` row layout,
    `.si-chip`, `.si-btn-primary` (blue-600), `.si-btn-ghost` (white/gray border).
  - Hide Streamlit default chrome narrow: no top-right menu, collapsed default
    if needed.
- `nav_items()` -> list of dicts `{id, label, icon}`: overview, ingestion,
  find, chat, analytics(→overview now), divider, demo_settings.

---

## 3. CHROME — sidebar + header — `components/chrome.py`

`render_sidebar() -> current_page_id`:
- `st.sidebar.markdown` with logo block: brain icon in white rounded badge +
  "SOLUTION INTELLIGENCE ENGINE" small-caps bold white.
- Nav rows: for each item, a button-style element. Simplest robust approach with
  Streamlit: a `st.radio` styled to look like nav (hide default radio dots) OR
  `st.button` per item inside a `st.container`. Decision: **`st.radio` styled
  via CSS** (one widget, on_change hook, reliable active-state) with label vs
  value mapping. Keys preserved in `st.session_state["page"]`.
- "System Status" bottom card: green dot + "All systems operational", 
  "Compute Speed: GPU Level 2" (from global state), "Dataset Size: Small (8)"
  (from global state).
- Demo settings belongs to this card (or below divider): GPU level `st.selectbox`
  and dataset size `st.radio` bound to global session keys
  (`gpu_level`, `dataset_size`) — these drive global state used by header + pages.

`render_header(page_id, subtitle)`:
- Container at top of main area: left title "Solution Intelligence Engine"
  (or "Chat with Intelligence Engine" on chat page) + page subtitle tagline
  (per spec). Right cluster: "Compute Speed" label + selectbox (GPU Level 2 ▾),
  and a 2x2 control grid (Play / Skip / End — Pause removed) via
  `components/playback.playback_buttons()`.
- Title/subtitle per page:
  - Overview: "Ingest. Understand. Retrieve. Respond."
  - Ingestion: "Watch the pipeline process records in real time."
  - Find a Solution: "Search and discover solutions from the knowledge base."
  - Chat: "Ask questions in natural language. Get answers with sourced solutions."

---

## 4. PLAYBACK — `components/playback.py`

State (session):
- `ss["playback"] = {"playing": False, "ended": False, "cur": 0, "phase": 0,
  "records_done": 0, "added": 0, "rejected": 0}` — reset when dataset/GPU change.

`playback_buttons(engine)`:
- Play (blue primary) → `ss["playback"]["playing"] = True` + `st.rerun()`.
- Skip → advance current record (if playing, jump to next record's keyframe;
  if idle, advance record index +1).
- End → `ss["playback"]["ended"] = True`, `playing=False` + `st.rerun()`.
- All rendered as `st.button` styled like spec (blue for Play).

`render_pipeline_animation(engine, container_height=...)`:
- Builds `views` from `engine.last_run` (reuse existing `_build_record_views`
  logic moved into this module as `build_record_views(run)`).
- Serializes views into a JSON blob:
  `payload = {"records": [{id, source, source_type, title, description,
  resolution, checks: [{stage,label,result,score}], outcome}], "gpu_delay": ...}`
- Wraps payload in the self-contained HTML/CSS/JS template (see §HTML below).
- Renders with `st.iframe(html_string, height="content", width="stretch")`
  (replaces `st.components.v1.html`).
- The `height="content"` mode auto-sizes the iframe to the HTML content height.

### HTML/JS animation template — `components/anim_template.html` (string constant)
- Uses the inline `data:` payload via `document.currentScript` adjacent JSON or
  a quoted JSON string embedded in the HTML (escaped for safety).
- Structure (Ingestion Pipeline page):
  - Left panel **Current Record**: source icon+label+ID, title, meta line,
    "DESCRIPTION:", body streams in with a **typewriter effect**
    (CSS `clip-path`/interval-based char reveal + blinking cursor).
  - Right panel **Pipeline Progress**: 4 sub-cards (Stage 1, AI Judge,
    Duplicate, Result) each with colored circular icon, status word,
    timestamp; Result card shows animated blue dots while pending, flips to
    green check / amber warning / red slash when the record verdict lands.
  - Below: horizontal progress bar filling to % (blue fill, gray track).
  - Row 2 **Live Tally**: 3 stat numbers updated by JS as records finish.
  - Row 3 **Recent Processed Records**: a `<table>` that appends rows as
    records complete (source, title, status badge, time=“Xs ago”).
- Timeline: per record — typewrite description (duration = gpu delay scaled by
  length), then reveal Stage1, Judge, Duplicate sequentially (delay = gpu
  delay), then verdict row appears, tally + recent table update, then next
  record. End of all records: swap to a "completed" banner (or the `End`
  button takes the user to static summary).
- No `st.rerun()` churn — the whole animation runs in the browser; when done it
  sets `ss["playback"]["finished_flag"]` via a small JS postMessage that app.py
  listens for (`components/html_message` wrapper) OR simpler: Play runs the
  animation, and when JS finishes it simply stops; the static summary page is
  reached via the `End` button or an auto "Show summary" button inside the
  HTML. Decision: keep it decoupled — the HTML shows its own completion state,
  and the End button always shows static summary. (No postMessage bridge.)

Security: payload is constructed from trusted demo data only (local JSON), so
`st.iframe` raw-HTML embedding warning is acceptable for this demo.

---

## 5. PAGE 1 — OVERVIEW — `components/overview.py`

Rendered with live data from `engine.index.entries` (existing analytics module
reused, NOT the deferred analytics page):
- Row 1 — 4 stat cards: Processed (len steps grouped by entry), Added
  (run.ingested), Rejected (run.rejected), Avg. Processing Time (mock 3.2s or
  0 if no run). Deltas: static demo text ("+12 today", "78.7%", "21.3%",
  "-0.8s vs yesterday").
- Row 2 — 3 cards:
  - **Ingestion Summary (Today)**: donut via pure CSS/SVG (conic-gradient ring)
    Added/Rejected/Processing with legend rows + Total.
  - **Top Categories**: horizontal bar list from `analytics.top_categories`
    (label left, blue gradient bar scaled to max, value right).
  - **Before vs After**: 3 stacked rows, label left + green % right, sub-line
    "Before: X → After: Y".
- Row 3 — Recent Activity table: Source | Record/Title | Category | Status |
  Time (from last run steps, newest first, status badge mapping
  PASS→Added green, FLAG→Review amber, REJECT→Rejected red).

Builders in `widgets.py` produce the HTML strings; page passes values.

---

## 6. PAGE 2 — INGESTION PIPELINE — `components/pipeline.py`

- If `ss["playback"]["playing"]`:
  - Run `playback.render_pipeline_animation(engine)` in main content (iframe).
  - Under it (native Streamlit, static section) the spec is satisfied mostly
    inside the iframe; native fallback table "Recent Processed Records" can be
    skipped since the iframe table covers it. Decision: iframe owns all
    pipeline content when playing.
- Else if `ss["playback"]["ended"]`:
  - Render static summary (replaces old `summary.py`; new `_static_summary` in
    this module): donut + tally metrics + per-stage breakdown +
    Recent Processed Records table (native Streamlit cards/tables, matching
    widgets.py). "View full history" link is a stub (`#`).
- Else (idle before first Play):
  - Empty-state hero card: "Ready to watch the pipeline work — press ▶ Play"
    + big Play button (calls the same handler).

---

## 7. PAGE 3 — FIND A SOLUTION — `components/solution_finder.py`

- Search input (default value "email not syncing on mobile") + blue Search
  button → `engine.search(query, top_k=5)`.
- Filter row: 3 left dropdowns (All Categories / All Sources / All Time) + right
  "Sort by: Relevance" dropdown. Categories & sources derived from data
  (`analytics.source_breakdown`, category set). Time filter is cosmetic.
- Top Matches list: each result = row card: green % match pill, bold title,
  gray description line, meta "Source: X · Date · Category: Y", outlined blue
  "View Details" button (buttons are `st.button` per row inside a
  `st.expander`-like CSS card; details could expand an inline panel or just a
  stub). Decision: "View Details" toggles a native `st.session_state`-backed
  `st.expander("Resolution", expanded=...)`.
- Footer: "Can't find what you need? **Ask the Engine**" link → sets page=chat.
- Right sidebar panel "Refine Search": chips for Suggested Keywords (clicking a
  chip inserts it into search input then runs search) + Related Categories
  chips with counts.

---

## 8. PAGE 4 — CHAT — `components/chat.py`

- Layout: `st.columns([3,1])` → chat column + Conversation History sidebar.
- Chat column (only basic bubble styling — accept native for now):
  - History: `st.chat_message` user (right, blue-50) / assistant (left,
    card) using `engine.agent` sessions (existing `ChatSession`).
  - Assistant message pattern per spec: answer paragraph, numbered steps,
    success line, Sources (blue links), footer thumbs/thumbs-down/share +
    timestamp (static icons only, cosmetic).
  - Input bar: `st.chat_input("Ask a follow-up question...")` →
    `engine.agent.respond(...)`.
  - Suggested follow-up chips: 3 st.button pills that prefill the input.
- Right sidebar: stacked history rows (question + relative time) +
  "🗑 Clear History" button → clears `ss["messages"]`/session.

---

## 9. DELETE / REWRITE CHANGELOG

- `src/solution_intelligence/constants.py` → replaced by `theme.py`.
  (`components/__init__.py` re-exports update accordingly.)
- `components/animation_state.py`, `header.py`, `playback_controls.py`,
  `record_view.py`, `summary.py` → deleted; logic folded into new modules.
- `app.py` → rewritten: main() + `page = render_sidebar()` + dispatch to the 4
  page renderers + shared header; no more `time.sleep`/`st.rerun` animation.
- `__init__.py` top-level API unchanged (SolutionEngine etc. still exported);
  `constants` import removed if referenced anywhere else (check agents/analytics).
- `data/knowledge.json` unchanged.

---

## 10. TESTING / VALIDATION

Per AGENTS.md:
- Unit tests: existing `tests/unit/test_engine.py`, `test_service.py` must stay
  green (`just test` / `uv run pytest tests/`).
- New coverage only where behavior changed in service layer — none expected
  (backend untouched). If any pure functions (e.g. `build_record_views`,
  `build_css`, widget HTML builders) warrant tests, add minimal ones in
  `tests/unit/test_ui_widgets.py`.
- Lint/format/type: `uv run ruff check src`, `uv run ruff format --check`,
  `uv run pyright src/solution_intelligence` per AGENTS.md.
- Docs build: `just docs-build` if docs reference removed modules (grep
  `docs/` for `constants`, `summary`, `playback_controls`, `record_view`,
  `animation_state`, `header`).
- Smoke: `timeout 20 uv run streamlit run src/solution_intelligence/app.py`
  starts without Traceback; load each page by clicking nav (manual).

---

## 11. ORDER OF WORK

1. `theme.py` (tokens + css builder).
2. `components/widgets.py` (HTML builders).
3. `components/chrome.py` (sidebar + header).
4. `components/playback.py` (+ anim template with client-side JS).
5. `components/overview.py`.
6. `components/pipeline.py`.
7. `components/solution_finder.py`.
8. `components/chat.py`.
9. Rewrite `app.py`; delete old files.
10. `components/__init__.py` refresh.
11. Run checks: pytest, ruff, format, pyright, streamlit smoke, docs grep.
12. Fix fallout; report which checks ran.