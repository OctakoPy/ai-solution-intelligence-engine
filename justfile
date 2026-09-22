# -----------------------------------------------------------------------------
# 🧰 Solution Intelligence Engine — Justfile
# -----------------------------------------------------------------------------
# Common developer commands for uv + npm-based projects.
# Run `just <command>` (e.g., `just test`).
# -----------------------------------------------------------------------------

# Always use bash for consistency across OSes
set shell := ["bash", "-cu"]

# Default recipe (shown when running plain `just`)
default:
    @just --list

# Install dependencies (create/update virtualenv + node modules)
install:
    uv sync
    npm install

# Install all dependencies (including dev + docs groups)
install-all:
    uv sync --all-groups
    npm install

# Install development dependencies (create/update virtualenv + node modules)
install-dev:
    uv sync --dev
    npm install

# Update dependencies to latest allowed versions
update:
    uv lock --upgrade
    npm update

# Regenerate lock files
lock:
    uv lock

# Lint (Ruff check)
lint:
    uv run ruff check .

# Format (Ruff format)
format:
    uv run ruff format .

# Verify formatting without changing files
format-check:
    uv run ruff format --check .

# Type checking (Pyright)
type-check:
    uv run pyright

# Run quick tests (exclude slow)
test:
    uv run pytest -q -m "not slow" --maxfail=1 --disable-warnings

# Run tests with verbose output (exclude slow)
test-vv:
    uv run pytest -vv -m "not slow" --maxfail=1 --disable-warnings

# Run the fast, non-mutating handoff checks
check: format-check lint type-check test

# Test notebooks
test-notebooks:
    uv run pytest --nbmake notebooks/

# Run full test suite with coverage
coverage:
    uv run pytest --cov --cov-report=term-missing

# Run the pilot evaluation (three ranking modes over the labeled demo cases)
eval:
    uv run python scripts/run_eval.py

# Build docs (MkDocs strict)
docs-build:
    uv run --group docs mkdocs build --strict

# Serve docs locally
docs-serve:
    uv run --group docs mkdocs serve -a localhost:8001

# Install pre-commit hooks
pre-commit-install:
    uv run pre-commit install \
    && uv run pre-commit autoupdate --repo https://github.com/pre-commit/pre-commit-hooks \
    && uv run pre-commit install -t pre-push \
    && uv run pre-commit install --hook-type commit-msg

# Run all pre-commit hooks
pre-commit:
    uv run pre-commit run --all-files --hook-stage push

# Clean generated artifacts
clean:
    rm -rf .pytest_cache dist build .ruff_cache .mypy_cache site
    rm -rf node_modules apps/web/node_modules apps/web/dist .vite

# Build distribution (wheel + sdist)
build:
    uv build

# Build, install, and import the package in a clean temporary environment
package-smoke-test:
    uv run --no-sync python scripts/package_smoke_test.py

# Run the comprehensive local equivalent of CI (excluding its OS/Python matrix)
ci: pre-commit coverage docs-build package-smoke-test

# Start Jupyter lab from inside a container
jupyter-devcontainer:
    uv run jupyter lab --allow-root --ip 0.0.0.0 --no-browser

# -----------------------------------------------------------------------------
# Solution Intelligence Engine — Frontend + API recipes
# -----------------------------------------------------------------------------

# Run the FastAPI backend in dev mode
api:
    uv run --no-sync uvicorn apps.api.main:app --reload --port 8004

# Run the Vite dev server (proxies /api → localhost:8004)
web:
    cd apps/web && npm run dev

# Run both API and web dev servers concurrently
dev:
    uv run --no-sync uvicorn apps.api.main:app --port 8004 &
    cd apps/web && npm run dev

# Build the Vite frontend
web-build:
    cd apps/web && npm run build

# Type-check the frontend
web-typecheck:
    cd apps/web && npm run typecheck

# Lint the frontend
web-lint:
    cd apps/web && npm run lint

# Run frontend unit tests
web-test:
    cd apps/web && npm run test

# Run Playwright e2e tests (assumes api + web are running)
web-e2e:
    cd apps/web && npm run e2e

# Combined local CI for backend + frontend
check-all: format-check lint type-check test web-typecheck web-lint web-build
