# Solution Intelligence Engine — Build Spec

Reference: 4-page demo dashboard mockup. Instructions below are self-contained (no image access needed).

---

## 0. GLOBAL DESIGN SYSTEM

### Colors
| Token | Hex | Usage |
|---|---|---|
| `navy-900` | `#0C172F` | Sidebar background |
| `navy-700` | `#1A366B` | Sidebar active nav item bg, "GPU Level 2" pill text |
| `blue-600` | `#175FEE` | Primary buttons (Play), links, progress bar fill, chat bubble accents |
| `blue-50` | `#EAF1FF` | User chat bubble background, hover states |
| `green-600` | `#0E9354` | Success text/badges ("Added", "Passed"), positive deltas, donut "Added" slice |
| `red-500` | `#E5484D` | Error/rejected badges, negative-status icon, donut "Rejected" slice (soft pink-red `#F4A6AC`) |
| `amber-500` | `#FDB84E` | Warning/"Review" badges and icons |
| `gray-900` | `#111827` | Primary heading text |
| `gray-500` | `#6B7280` | Secondary/meta text (timestamps, labels) |
| `gray-200` | `#E5E7EB` | Borders, dividers, track backgrounds |
| `gray-50` | `#F7F8FA` | Page background (outside cards) |
| `white` | `#FFFFFF` | Card backgrounds, sidebar active-item icon |

### Typography
- Font: system sans-serif (Inter / SF Pro style) — clean geometric grotesque.
- Page title: 20–22px, bold, `gray-900`.
- Page subtitle (tagline under title): 13px, regular, `gray-500`.
- Card title: 14–15px, semibold, `gray-900`.
- Body/table text: 13px, regular.
- Metric big numbers: 26–28px, bold.
- Labels/meta (timestamps, source tags): 11–12px, `gray-500`.
- Small link text (e.g. "View all", "View Details"): 12–13px, `blue-600`, medium weight.

### Layout shell (applies to all 4 pages)
- **Left sidebar**: fixed width ~240px, `navy-900` background, full height.
  - Top: logo mark (brain/circuit icon in a white rounded badge) + product name "SOLUTION INTELLIGENCE ENGINE" in white, small-caps/bold, 3-line wrap, letter-spacing wide.
  - Nav list (white icon + label, 8px vertical padding each):
    1. Overview (house icon)
    2. Ingestion Pipeline (refresh/cycle icon)
    3. Find a Solution (magnifier icon)
    4. Chat with the Engine (speech-bubble icon)
    5. Analytics (bar-chart icon)
    — divider —
    6. Demo Settings (gear icon)
  - Active item: `navy-700` rounded-rectangle background behind the row, white bold text.
  - Inactive items: light gray/white-70% text, no background.
  - Bottom-pinned card (`navy-700`-ish darker panel, subtle border): "System Status"
    - Green dot + "All systems operational"
    - "Compute Speed: GPU Level 2" (value in light blue)
    - "Dataset Size: Small (8)" (value in light blue)
- **Top header bar** (repeats on every page, inside main content area, white bg):
  - Left: small brain icon + page/product title "Solution Intelligence Engine" (bold, 20px) — on the Chat page this becomes "Chat with Intelligence Engine".
  - Under title: one-line gray subtitle tagline, page-specific (see below).
  - Right side: a control cluster —
    - "Compute Speed" label above a dropdown select showing "GPU Level 2 ▾"
    - 2x2 button grid: **Play** (solid `blue-600` bg, white text, ▶ icon — this is the primary/active button), **Pause** (white bg, gray border, ⏸ icon), **Skip** (white bg, gray border, ⏭ icon), **Restart** (white bg, gray border, ⟳ icon).
- **Main content area**: `gray-50`/white background, generous 24px padding, cards use white bg, 1px `gray-200` border, 8–12px border-radius, subtle shadow.
- Section header pattern inside cards: bold title left, optional blue "View all →" link right-aligned.

### Reusable components
- **Stat card**: icon (colored, matches metric semantic) + label (top), big number (middle), small delta/sub-stat text below in green/gray.
- **Status badge**: colored dot/icon + colored text, no pill background — just icon+text pairing (green check = Added/Passed, amber triangle = Review, red circle-slash = Rejected).
- **Donut chart**: ring chart, legend to the right (colored dot + label + % + count), "Total" row below legend.
- **Horizontal bar list** ("Top Categories" style): label left, blue bar (rounded), value right-aligned, bars scaled to max value, track in light gray.
- **Data table**: header row gray-500 uppercase-ish small text, rows separated by hairline dividers, no zebra striping, status column uses Status Badge.
- **Pill/tag input chip** (used in Find a Solution "Suggested Keywords"/"Related Categories"): white bg, gray-200 border, rounded-full or rounded-md, black text, optional count in parens.

---

## 1. PAGE — OVERVIEW (default/landing route)

Subtitle under title: "Ingest. Understand. Retrieve. Respond."

**Row 1 — 4 stat cards, equal width, horizontal:**
1. Processed Records — 1,248 — sub: "+12 today" (green)
2. Added to Knowledge Base — 982 — sub: "78.7%" (gray)
3. Rejected / Duplicates — 266 — sub: "21.3%" (gray)
4. Avg. Processing Time — 3.2s — sub: "-0.8s vs yesterday" (green)

**Row 2 — 3 cards, roughly 30/35/35 width split:**
- **Ingestion Summary (Today)**: donut chart. Segments: Added 78.7% (982) green, Rejected 21.3% (266) red/pink, Processing 0.0% (0) blue. Legend rows list color-dot, label, %, count. Footer row: "Total — 1,248".
- **Top Categories** (header has "View all" link): horizontal bar list — Access/Login 324, Software/App 287, Email/Outlook 193, Hardware 158, Others 120. Bars are blue, proportional to 324 max.
- **Before vs After (Impact)**: 3 stacked metric rows, each with label left + bold green percentage right (e.g. "-42%", "-51%", "-37%"), and a "Before: X → After: Y" sub-line under each:
  - Avg. Time to Resolve: Before 12.1 min → After 7.0 min (-42%)
  - Repeat Tickets: Before 28% → After 13.7% (-51%)
  - Agent Escalations: Before 18% → After 11.3% (-37%)

**Row 3 — full-width Recent Activity table:**
Columns: Source | Record/Title | Category | Status | Time
Sample rows:
- Ticketing System | Email not syncing on mobile device | Email/Outlook | ✅ Added | 2 min ago
- SAP System | User role access issue | Access/Login | ✅ Added | 4 min ago
- SharePoint | Cannot access shared folder | Access/Login | ⚠️ Review | 7 min ago
- Knowledge Base | Outlook app crashing on launch | Software/App | ❌ Rejected | 9 min ago

---

## 2. PAGE — INGESTION PIPELINE

Same header shell. Page label "2. Ingestion Pipeline" is only an external annotation, not shown in-app — in-app just uses the standard header.

**Row 1 — two panels side by side (roughly 35/65 split):**

- **Current Record** (left panel):
  - Ticket icon + "Ticketing System" + right-aligned ticket ID "#INC-000345"
  - Bold title: "Email not syncing on mobile device"
  - Meta line: "Category: Email/Outlook · Date: 23 May 2025"
  - "DESCRIPTION:" label (bold, small, uppercase) + paragraph: user report text about mobile sync issue after update, restart attempted.
  - "RESOLUTION:" label + paragraph: cache cleared, re-synced account, fixed after re-auth and removing outdated sync settings. (cursor blink indicator at end suggests this streams in live)

- **Pipeline Progress** (right panel):
  - 4 equal sub-cards in a row, each: stage title (e.g. "Stage 1 / Structural Check"), colored circular status icon, status word, timestamp:
    1. Stage 1 / Structural Check — green check — "Passed" — 23 May 2025 10:21:15
    2. AI Judge / Quality Check — green check — "Passed" — 23 May 2025 10:21:18
    3. Duplicate / Similarity Check — amber warning triangle — "Review" — 23 May 2025 10:21:21
    4. Result — animated blue dots spinner — "Waiting"
  - Below the 4 sub-cards: full-width horizontal progress bar, blue fill to ~75%, gray track, "75%" label right-aligned.

**Row 2 — Live Tally panel (full width, 3-column stat row inside one card):**
- Processed: 24
- ✅ Added: 18
- 🚫 Rejected: 6

**Row 3 — Recent Processed Records table (full width, header has "View full history" blue link top-right):**
Columns: Source | Record/Title | Status | Time
- Ticketing System | Outlook app crashing on launch | ✅ Added | 1 min ago
- SAP System | Password reset not working | ✅ Added | 3 min ago
- SharePoint | Cannot access shared folder | ⚠️ Review | 7 min ago

---

## 3. PAGE — FIND A SOLUTION (search)

Section heading inside content: "Find a Solution" (bold) + subtitle "Search and discover solutions from the knowledge base."

**Search bar row:** full-width text input with magnifier icon, placeholder/value "email not syncing on mobile", solid blue "Search" button to its right.

**Filter row** directly below: 3 left-aligned dropdown filters — "All Categories ▾", "All Sources ▾", "All Time ▾" — and one right-aligned dropdown — "Sort by: Relevance ▾".

**Main column — "Top Matches" list** (each result is a row/card):
Each result: green % match badge (pill, white text on green, e.g. "98%"), bold title, one-line gray description, meta line "Source: X · Date · Category: Y", and a right-aligned outlined "View Details" button (blue text, blue border).
1. 98% — Email not syncing on mobile device — "Clear app cache and re-sync account. Issue resolved after re-authentication and removing old sync settings." — Source: Ticketing System · 23 May 2025 · Category: Email/Outlook
2. 95% — Outlook mobile app not updating emails — "Check Outlook sync settings and ensure background refresh is enabled. Re-add account if issue persists." — Source: Knowledge Base · 12 Apr 2025 · Category: Email/Outlook
3. 92% — Mobile email sync delay after update — "Delay caused by cached credentials. Sign out and sign in again to refresh token." — Source: SharePoint · 05 May 2025 · Category: Email/Outlook

Footer line under list: "Can't find what you need? **Ask the Engine**" (link in blue, routes to Chat page).

**Right sidebar panel — "Refine Search":**
- "Suggested Keywords" — 4 chip buttons stacked vertically, full width, white bg/gray border: "Outlook mobile sync", "Email sync delay", "Mobile email not updating", "Outlook app sync issue"
- "Related Categories" — 3 chip buttons with counts: "Email/Outlook (324)", "Access/Login (287)", "Software/App (193)"

---

## 4. PAGE — CHAT WITH THE ENGINE

Header title becomes "Chat with Intelligence Engine". Subtitle: "Ask questions in natural language. Get answers with sourced solutions."

**Layout: main chat column (~75% width) + right sidebar "Conversation History" (~25% width).**

**Chat column:**
- User message: right-aligned bubble, `blue-50` bg, dark text, timestamp bottom-right inside/below bubble. Example: "Why are my emails not syncing on my mobile after the update?" — 10:21 AM
- Assistant message: left-aligned, small circular bot avatar icon, white/gray-50 card bubble, contains:
  - Answer paragraph: "This issue is usually caused by cached authentication or sync settings. Here are the steps that resolved it for similar cases:"
  - Numbered list: 1. Clear app cache 2. Re-authenticate your account 3. Re-sync emails
  - Line: "This solved the issue in 98% of similar cases."
  - "Sources:" label + bulleted list of blue links: "Email not syncing on mobile device (Ticketing System) – 23 May 2025 (98%)", "Outlook mobile app not updating emails (KB Article) – 12 Apr 2025 (95%)"
  - Footer row: thumbs-up / thumbs-down / share icons (gray, small) left, timestamp right ("10:21 AM")
- **Follow-up input bar** (pinned below message list): full-width rounded text input, placeholder "Ask a follow-up question...", circular blue send-arrow button on the right.
- **Suggested follow-up chips** below input: 3 outlined pill buttons, blue text/border: "How to clear cache in Outlook mobile?", "Re-authentication steps", "Still not working, what next?"

**Right sidebar — "Conversation History":**
- Stacked list items (card rows), each: question text (bold-ish, 2 lines max) + timestamp/relative-date bottom-right ("10:21 AM" / "Yesterday"):
  1. "Why are my emails not syncing on mobile?" — 10:21 AM
  2. "How to reset Outlook sync settings?" — Yesterday
  3. "Fix for mobile email sync delay" — Yesterday
- Bottom: full-width outlined button "🗑 Clear History".

---

## 5. NAVIGATION / STATE NOTES FOR BUILD
- Sidebar nav is shared across all routes; highlight state changes per route (this mock shows "Overview" active on all 4 screenshots except conceptually each page should self-highlight).
- Play/Pause/Skip/Restart controls appear identical on every page — treat as a shared header component; likely controls a simulated/demo data feed (Play = start streaming demo events, Skip = jump record, Restart = reset counters).
- "GPU Level 2" dropdown and System Status panel values are shared global app state, not per-page.
- Data throughout is mock/demo data — wire to real API endpoints matching the same shape (records, categories, pipeline stages, chat turns).
