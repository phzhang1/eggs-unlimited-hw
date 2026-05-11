# Phase 1 — Project Bootstrap

## Goal
Create a runnable, empty FastAPI shell that a fresh-clone reviewer can install and start with three commands. Implement `GET /healthz` (the only endpoint in this phase) so the "starts in suggested env without code mods" rubric point is verifiable on day one.

## Inputs (must read first)
- [AGENTS.md](../AGENTS.md) §3 (locked tech stack), §6.1 (single `app.py`), §6.9 (logging — uvicorn default), §6.13 (run command), §6.14 (repo hygiene), §7 (rubric mapping)
- [phases/00-readme-skeleton.md](00-readme-skeleton.md) — outputs (the `README.md` should already exist; do not rewrite it, just confirm Quick Start commands match what you set up)

## Deliverables
- `.gitignore` — excludes `.venv/`, `__pycache__/`, `*.db`, `.pytest_cache/`, `.DS_Store`, `*.egg-info/`
- `requirements.txt` — pinned versions of `fastapi`, `uvicorn[standard]`, `pytest`, `httpx` (httpx is required by FastAPI's `TestClient`; pin so the grader's install is deterministic)
- `app.py` — minimal FastAPI app: imports `FastAPI`, instantiates `app`, defines `@app.get("/healthz")` returning `{"status": "ok"}`. **No other routes yet.**
- `static/index.html` — temporary placeholder file with one line of text (e.g., `<h1>Eggs Unlimited — coming soon</h1>`). Mounted at `/` via `app.mount("/", StaticFiles(directory="static", html=True), name="static")`. Phase 4 replaces the contents; the mount line stays.
- `.venv/` — created locally (NOT committed; `.gitignore` covers it)

## Steps
1. From the workspace root:
   ```bash
   python3.11 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install fastapi 'uvicorn[standard]' pytest httpx
   pip freeze > requirements.txt
   ```
2. Inspect `requirements.txt`. Trim it to only the four direct dependencies and their transitive deps that pip actually installed. (Don't hand-edit pins — pip already resolved them.)
3. Write `.gitignore` (see Deliverables above).
4. Write `static/index.html` placeholder.
5. Write `app.py`:
   ```python
   from fastapi import FastAPI
   from fastapi.staticfiles import StaticFiles

   app = FastAPI(title="Eggs Unlimited")


   @app.get("/healthz")
   def healthz():
       return {"status": "ok"}


   app.mount("/", StaticFiles(directory="static", html=True), name="static")
   ```
   The `StaticFiles` mount must be **last** (after all `@app.get`/`@app.post` routes) — FastAPI evaluates routes in registration order, and a root-mounted static handler will swallow every path otherwise.
6. Verify from a *fresh terminal* (so you exercise activation):
   ```bash
   source .venv/bin/activate
   uvicorn app:app --reload
   ```
7. In a second terminal:
   ```bash
   curl -i localhost:8000/healthz
   curl -I localhost:8000/
   ```
8. In the uvicorn terminal, confirm the access log shows lines like `INFO: 127.0.0.1:xxxxx - "GET /healthz HTTP/1.1" 200 OK`. This satisfies the "console logs include method/path/status" requirement (per AGENTS.md §6.9) without any custom middleware.
9. Stop uvicorn (Ctrl-C), restart it, hit `/healthz` again. Confirm it still works after restart — this is the rehearsal for the persistence rubric point even though we have no DB yet.

## Exit criteria
- `pip install -r requirements.txt` in a brand-new venv succeeds.
- `uvicorn app:app --reload` starts without errors.
- `curl localhost:8000/healthz` returns HTTP 200 and JSON body `{"status":"ok"}`.
- Visiting `http://localhost:8000/` in a browser shows the placeholder text.
- Uvicorn's default access log prints `METHOD path -> status` lines for each request.
- The README's Quick Start commands (from Phase 0) match exactly what you ran. If they don't, fix the README to match (don't change reality to fit the README).

## Walkthrough defense notes
- "Why pin transitive deps in `requirements.txt`?" — Reproducibility: if FastAPI ships a breaking 0.116 next week, the grader's machine still installs the same versions you developed against.
- "Why not Poetry / uv / pip-tools?" — Take-home scope. A pinned `requirements.txt` and a venv is the lowest-friction installer the grader will see, and matches the rubric line "starts in suggested env without code mods."
- "Why is `StaticFiles` mounted last?" — Routes register in order; a `/`-mounted catch-all has to come after the explicit API routes or it intercepts them.

## Out of scope for this phase
- **No data model**, no Pydantic classes, no SQLite schema. Phase 2 owns those.
- **No `/submit`, `/entries`, `/export.csv` routes.** Phase 3.
- **No real frontend.** The placeholder `index.html` is one line; Phase 4 replaces it.
- **No tests.** Phase 5.
- **No `Dockerfile`, no Makefile, no `pyproject.toml`** — AGENTS.md §5 vetoes these.
- **Don't over-pin Python.** `requirements.txt` is package versions only; the Python version (3.11+) lives in the README.
