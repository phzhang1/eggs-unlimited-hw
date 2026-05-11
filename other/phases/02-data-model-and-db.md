# Phase 2 — Data Model & DB Layer

## Goal
Add the Pydantic `EggRequest` model (with enum types), the SQLite schema (one `entries` table with `CHECK` constraints), the per-request connection dependency, and the lifespan hook that runs `CREATE TABLE IF NOT EXISTS` on startup. After this phase the database file exists and is shaped correctly, but no endpoint reads or writes it yet.

## Inputs (must read first)
- [AGENTS.md](../AGENTS.md) §6.2 (flat Pydantic + enums), §6.3 (denormalized table + CHECK constraints), §6.4 (connection-per-request), §6.5 (validation strategy: Pydantic + DB CHECK + HTML5 `required`)
- [hw.md](../hw.md) — `Form fields` section for the 13 fields and their enum values; `Validation` section for which fields are required vs. optional
- [phases/01-bootstrap.md](01-bootstrap.md) — outputs (`app.py` already exists with `/healthz` and the `StaticFiles` mount)

## Deliverables
- Updated `app.py` containing:
  - Python `Enum` classes: `EggType`, `EggSize`, `EggGrade`, `EggPack`
  - Pydantic `EggRequest` model — flat, all 13 fields, required vs. `Optional[...]` matching `hw.md`'s validation rules
  - Constant `DB_PATH = "entries.db"`
  - `init_db()` function with `CREATE TABLE IF NOT EXISTS entries (...)` including:
    - `id TEXT PRIMARY KEY`
    - one column per Pydantic field (TEXT for strings/enums, REAL for `quantity_value` and `price_per_dozen`, TEXT for optional dates)
    - `created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP`
    - `CHECK (type IN ('Conventional','CageFree','FreeRange','Organic'))` and equivalent for `size`, `grade`, `pack`
    - `NOT NULL` on the required fields
  - FastAPI `lifespan` async context manager that calls `init_db()` on startup
  - `get_db()` dependency function: `conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row; try: yield conn; finally: conn.close()`

## Steps
1. Reread the form-fields list in `hw.md` and write down the 13 field names exactly as they'll appear in the schema. Suggested snake_case mapping:
   ```
   farm_name, contact, phone_email, location,
   type, size, grade, pack,
   quantity_value, quantity_unit, price_per_dozen,
   available_start, available_end, notes
   ```
   Note: `contact` and `phone_email` look duplicative in the spec — `contact` = a name (required), `phone_email` = a phone or email (optional). Keep both; add a one-line comment in `app.py` explaining the distinction so a reviewer doesn't ask.
2. Define the four `Enum` classes near the top of `app.py`. Each enum value's *string* must match exactly the spec wording (`"Conventional"`, `"CageFree"`, `"FreeRange"`, `"Organic"`, `"AA"`, `"A"`, `"B"`, `"12ct_carton"`, `"18ct_carton"`, `"24ct_tray"`, `"30dozen_case"`, etc.).
3. Define `EggRequest(BaseModel)` with:
   - Required fields as plain types (`str`, `EggType`, `float`, ...)
   - Optional fields as `phone_email: str | None = None`, `available_start: str | None = None`, etc. (Use `str` for the date fields for now — Pydantic will accept any string and the spec doesn't require date parsing. Document this trade-off in the Phase 6 README pass.)
   - `quantity_value: float` and `price_per_dozen: float` — Pydantic auto-rejects non-numeric input.
4. Write `init_db()`. Single multi-line `cur.execute("""CREATE TABLE IF NOT EXISTS ...""")` followed by `conn.commit()`. Use the same `DB_PATH`.
5. Wire `init_db()` to FastAPI's lifespan:
   ```python
   from contextlib import asynccontextmanager

   @asynccontextmanager
   async def lifespan(app: FastAPI):
       init_db()
       yield

   app = FastAPI(title="Eggs Unlimited", lifespan=lifespan)
   ```
   Use the modern `lifespan=` parameter; `@app.on_event("startup")` is deprecated.
6. Add `get_db()` dependency near the bottom of `app.py` (above the `StaticFiles` mount). Per AGENTS.md §6.4:
   ```python
   def get_db():
       conn = sqlite3.connect(DB_PATH)
       conn.row_factory = sqlite3.Row
       try:
           yield conn
       finally:
           conn.close()
   ```
   `row_factory = sqlite3.Row` makes rows behave like dicts — Phase 3 needs that for JSON serialization.
7. Restart uvicorn. Confirm no errors on startup. Then verify the schema from the CLI:
   ```bash
   sqlite3 entries.db ".schema"
   sqlite3 entries.db "PRAGMA table_info(entries);"
   ```
   The `.schema` output should show the full `CREATE TABLE` statement including all `CHECK` clauses.
8. Sanity-check a manual insert from the sqlite CLI to confirm the constraints fire:
   ```bash
   sqlite3 entries.db "INSERT INTO entries (id, farm_name, contact, location, type, size, grade, pack, quantity_value, quantity_unit) VALUES ('test', 'Acme', 'Jane', '94110', 'NotARealType', 'Large', 'AA', '12ct_carton', 12, 'dozen');"
   ```
   Expect: `Error: CHECK constraint failed: type`. Then `DELETE FROM entries WHERE id='test';` to clean up. (If the row inserted, your CHECK is wrong.)

## Exit criteria
- `app.py` contains the four enums, the `EggRequest` model, `init_db()`, the lifespan hook, and `get_db()`.
- `uvicorn app:app --reload` starts cleanly with no warnings about deprecated startup events.
- `sqlite3 entries.db ".schema"` shows the table with all CHECK constraints and the `created_at DEFAULT CURRENT_TIMESTAMP`.
- A manual `INSERT` with a bad enum value is rejected by SQLite.
- `/healthz` still returns 200 (didn't break Phase 1).

## Walkthrough defense notes
- "Why CHECK constraints in addition to Pydantic enums?" — Defense in depth. Pydantic guards the API boundary; CHECK guards anyone who connects to the DB directly (tests, sqlite CLI, future code paths). One line of SQL per enum.
- "Why `row_factory = sqlite3.Row`?" — So you can do `dict(row)` in Phase 3's `/entries` handler without writing a column-by-column converter.
- "Why `lifespan=` instead of `@app.on_event('startup')`?" — `on_event` is deprecated as of FastAPI 0.93; the lifespan async context manager is the current idiom (verify with [Exa](https://fastapi.tiangolo.com/advanced/events/) if challenged).
- "Why a per-request connection?" — SQLite + Python threads have `check_same_thread` rules; a fresh connection per request via `Depends(get_db)` is the simplest correct option for FastAPI's threadpool execution model.

## Out of scope for this phase
- **No `/submit`, `/entries`, or `/export.csv` routes.** Phase 3.
- **No custom validation error handler.** Phase 3.
- **No frontend changes.** Phase 4.
- **No data seeding.** The `entries` table starts empty — Phase 5's tests will populate it as needed.
- **No `connect_args={"check_same_thread": False}`** — that's a SQLAlchemy-with-shared-engine workaround; we use `sqlite3` directly with one connection per request, so it's unnecessary.
- **No SQLAlchemy, no SQLModel, no Alembic** — AGENTS.md §5 vetoes ORMs and migrations.
