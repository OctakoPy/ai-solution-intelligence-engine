@echo off
REM Start the Solution Intelligence Engine dev stack without `just`.
REM
REM   - FastAPI backend -> http://localhost:8004
REM   - Vite dev server -> http://localhost:5179  (proxies /api -> :8004)
REM
REM Closing this window (or Ctrl-C) stops both processes.
REM
setlocal

set ROOT=%~dp0..

set API_PID=
set WEB_PID=

echo === Solution Intelligence Engine — dev stack ===

echo Starting API on :8004 ...
start "sie-api" /B cmd /c "cd /d %ROOT% && uv run --no-sync uvicorn apps.api.main:app --port 8004 --reload"
set API_PID=

REM Give uvicorn a head start before Vite starts proxying.
ping 127.0.0.1 -n 3 >nul

echo Starting Vite on :5179 (api proxy -> http://localhost:8004) ...
start "sie-web" /B cmd /c "cd /d %ROOT%\apps\web && npm run dev"
set WEB_PID=

echo.
echo Backend  : http://localhost:8004/docs
echo Frontend : http://localhost:5179
echo.
echo Close the spawned windows (or this one) to stop the dev stack.
echo.

endlocal
