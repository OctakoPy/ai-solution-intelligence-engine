#!/usr/bin/env bash
#
# Start the Solution Intelligence Engine dev stack without `just`.
#
# Spawns:
#   - FastAPI backend  -> http://localhost:8004
#   - Vite dev server  -> http://localhost:5179  (proxies /api -> :8004)
#
# Ctrl-C in this terminal stops both processes.
#
set -euo pipefail

# Resolve repo root (script lives in <root>/scripts)
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_PID=""
WEB_PID=""

cleanup() {
  echo "→ stopping dev servers..."
  [ -n "$WEB_PID" ] && kill "$WEB_PID" 2>/dev/null || true
  [ -n "$API_PID" ] && kill "$API_PID" 2>/dev/null || true
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "→ starting API on :8004..."
(
  cd "$ROOT" &&
  uv run --no-sync uvicorn apps.api.main:app --port 8004 --reload
) &
API_PID=$!

# Give the backend a moment to boot before Vite starts proxying.
sleep 2

echo "→ starting Vite on :5179 (api proxy → http://localhost:8004)..."
(
  cd "$ROOT/apps/web" &&
  npm run dev
) &
WEB_PID=$!

echo
echo "→ Solution Intelligence Engine is starting up:"
echo "    API      : http://localhost:8004/docs"
echo "    Frontend  : http://localhost:5179"
echo
echo "    Press Ctrl-C to stop both."

wait
