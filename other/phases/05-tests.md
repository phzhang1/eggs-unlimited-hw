# Phase 5 — Tests

## Goal
Add a `tests/` directory with a `conftest.py` fixture that swaps the production DB for an isolated temp file via `app.dependency_overrides[get_db]`, and three lightweight `TestClient` tests covering health, happy-path round trip, and the friendly-validation-error shape. After this phase `pytest -v` is green and runs in well under a second.

## Inputs (must read first)
- [AGENTS.md](../AGENTS.md) §6.11 (three tests: healthz, happy path, missing-field 422), §7 (rubric: "at least one test")
- [phases/02-data-model-and-db.md](02-data-model-and-db.md) — `get_db()` is the dependency we will override; `init_db()` is the schema bootstrapper we will call against the test DB
- [phases/03-endpoints-and-validation.md](03-endpoints-and-validation.md) — defines the request/response shapes the tests assert against

## Deliverables
- `tests/__init__.py` — empty file (makes `tests/` a package; keeps `pytest` collection deterministic)
- `tests/conftest.py` — pytest fixture providing a `TestClient` wired to a per-test isolated SQLite file using `app.dependency_overrides`
- `tests/test_app.py` — three test functions

## Steps

### 1. `tests/__init__.py`
Empty file. Just `touch tests/__init__.py`.

### 2. `tests/conftest.py`
```python
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app as app_module


@pytest.fixture()
def client(tmp_path: Path):
    """A TestClient backed by a fresh, isolated SQLite file for each test.

    Why dependency_overrides: it's FastAPI's documented way to swap a Depends()
    target during tests without touching production code. Each test gets its
    own tmp_path so tests cannot leak state into each other.
    """
    db_path = tmp_path / "test_entries.db"

    def override_get_db():
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    # Initialize the schema against the test DB before any request runs.
    init_conn = sqlite3.connect(db_path)
    try:
        app_module.init_db_with_conn(init_conn) if hasattr(
            app_module, "init_db_with_conn"
        ) else _bootstrap_schema(init_conn)
    finally:
        init_conn.close()

    app_module.app.dependency_overrides[app_module.get_db] = override_get_db
    try:
        yield TestClient(app_module.app)
    finally:
        app_module.app.dependency_overrides.clear()


def _bootstrap_schema(conn: sqlite3.Connection) -> None:
    """Fallback that re-executes the same CREATE TABLE statement app.init_db
    runs at startup. If init_db only knows the production DB_PATH, we copy its
    SQL here. Keep these two definitions identical."""
    # If app.init_db is parameterless and hardcodes the path, the simplest
    # correct move is to refactor init_db to accept an optional connection
    # and call it directly. Prefer that over duplicating SQL here.
    raise RuntimeError(
        "Refactor app.init_db to accept an optional connection so the test "
        "fixture can call it without duplicating the CREATE TABLE SQL."
    )
```

**Note on the refactor:** if `app.init_db()` from Phase 2 is parameterless and opens its own connection against `DB_PATH`, give it an optional `conn` parameter:

```python
def init_db(conn: sqlite3.Connection | None = None) -> None:
    own_conn = conn is None
    conn = conn or sqlite3.connect(DB_PATH)
    try:
        conn.execute("""CREATE TABLE IF NOT EXISTS entries (...)""")
        conn.commit()
    finally:
        if own_conn:
            conn.close()
```

Then `conftest.py` simplifies to `app_module.init_db(init_conn)` and the fallback `_bootstrap_schema` can be deleted. **Do this refactor before writing the tests** — it's cleaner than carrying two copies of the schema.

### 3. `tests/test_app.py`
```python
VALID_PAYLOAD = {
    "farm_name": "Acme Farms",
    "contact": "Jane Doe",
    "phone_email": "jane@acme.example",
    "location": "94110",
    "type": "Organic",
    "size": "Large",
    "grade": "AA",
    "pack": "12ct_carton",
    "quantity_value": 12,
    "quantity_unit": "dozen",
    "price_per_dozen": 4.50,
    "notes": "Test entry",
}


def test_healthz(client):
    res = client.get("/healthz")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_submit_then_list_round_trip(client):
    # Submit two entries to also exercise the "more than one entry" rubric line.
    ids = []
    for i in range(2):
        payload = {**VALID_PAYLOAD, "farm_name": f"Acme {i}"}
        res = client.post("/submit", json=payload)
        assert res.status_code == 201, res.text
        body = res.json()
        assert "id" in body
        # uuid4 strings are 36 chars including hyphens.
        assert len(body["id"]) == 36
        ids.append(body["id"])

    listed = client.get("/entries")
    assert listed.status_code == 200
    rows = listed.json()
    assert isinstance(rows, list)
    listed_ids = {r["id"] for r in rows}
    assert set(ids).issubset(listed_ids)


def test_submit_missing_required_field_returns_friendly_422(client):
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "farm_name"}
    res = client.post("/submit", json=payload)
    assert res.status_code == 422

    body = res.json()
    # The custom validation handler returns {"errors": [{"field", "message"}]},
    # never the default {"detail": [...]} shape.
    assert "errors" in body
    assert "detail" not in body

    fields = {err["field"] for err in body["errors"]}
    assert "farm_name" in fields

    # Every error has both "field" and "message" populated.
    for err in body["errors"]:
        assert err["field"]
        assert err["message"]
```

### 4. Run from CLI
```bash
source .venv/bin/activate
pytest -v
```
Expect three passes, no warnings about deprecated APIs, total runtime well under 1s.

### 5. Sanity-check isolation
```bash
pytest -v   # run twice in a row; second run should also be 3/3 green
```
If a test pollutes the production `entries.db`, the second run will accumulate rows and the round-trip test could falsely "pass" by finding old IDs. The `tmp_path` fixture exists precisely to prevent this.

## Exit criteria
- `pytest -v` exits 0 with three passing tests.
- The production `entries.db` is **not modified** by running the test suite (check `ls -la entries.db` before/after; size and mtime unchanged). If it changes, the dependency override isn't applied.
- `pytest` is the only command needed — no env vars, no flags, no `--rootdir`, no `PYTHONPATH=`.
- The friendly-error test specifically asserts the `{"errors": [...]}` shape and the absence of `"detail"`. This guards against accidental regressions in Phase 3's exception handler.

## Walkthrough defense notes
- "Why three tests when the spec says one?" — Each test maps directly to a rubric line: healthz (200 OK), submit→list (data sent + listable + multiple entries), 422 (friendly-error bonus). Total cost is ~40 lines and proves competence beyond the bare minimum.
- "Why `tmp_path` instead of an in-memory `:memory:` database?" — `:memory:` SQLite databases are per-connection; with our per-request connection model, each request would see a fresh empty DB. A temp file behaves the same as the production DB but is isolated per test.
- "Why `app.dependency_overrides`?" — FastAPI's documented test pattern (`https://fastapi.tiangolo.com/advanced/testing-dependencies/`). Cleaner than monkey-patching `DB_PATH`, and the override automatically clears after the fixture's `yield`.
- "Why refactor `init_db` to take an optional connection?" — Avoids duplicating the `CREATE TABLE` SQL between `app.py` and the test fixture. One source of truth.

## Out of scope for this phase
- **No frontend tests.** No Playwright, Selenium, or Cypress — AGENTS.md §5 vetoes them and the rubric doesn't ask.
- **No coverage configuration.** No `pytest-cov`, no `.coveragerc`.
- **No parametrize-the-world tests.** Three focused tests are enough.
- **No CI configuration.** No `.github/workflows/`. Tests run locally for the walkthrough.
- **No database transaction-rollback fixture pattern.** That's a SQLAlchemy/sessionmaker idiom; with raw `sqlite3` and `tmp_path`, file-per-test is simpler and correct.
- **No mocking of `uuid.uuid4`.** The test asserts shape (`len == 36`), not specific values.
