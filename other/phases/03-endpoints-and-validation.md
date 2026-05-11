# Phase 3 — API Endpoints & Friendly Validation

## Goal
Implement the four data-bearing endpoints (`POST /submit`, `GET /entries`, `GET /export.csv`, `GET /exportcsv`) and the custom `RequestValidationError` handler that returns `{"errors": [{"field": ..., "message": ...}, ...]}`. After this phase the backend is functionally complete and verifiable end-to-end with `curl`.

## Inputs (must read first)
- [AGENTS.md](../AGENTS.md) §6.7 (export route alias), §6.8 (CSV via `csv.DictWriter` + `io.StringIO`), §6.10 (custom validation handler shape)
- [hw.md](../hw.md) — `Endpoints (minimum)` section confirms the response shape `{"id": "<uuid>"}` and lists `/exportcsv` (the spec uses both spellings)
- [phases/02-data-model-and-db.md](02-data-model-and-db.md) — `EggRequest` model, `get_db()` dependency, and the `entries` table all already exist

## Deliverables
- Updated `app.py`:
  - `POST /submit` — accepts `EggRequest` body, generates `uuid.uuid4()`, inserts a row, returns `{"id": "<uuid>"}` with HTTP 201
  - `GET /entries` — selects all rows, returns a JSON list of dicts (each row including `id` and `created_at`)
  - One `export_csv()` handler decorated with **both** `@app.get("/export.csv")` and `@app.get("/exportcsv")` — see AGENTS.md §6.7 — using `csv.DictWriter` + `io.StringIO`, returned as `Response(content=..., media_type="text/csv", headers={"Content-Disposition": 'attachment; filename="entries.csv"'})`
  - Custom `@app.exception_handler(RequestValidationError)` returning a `JSONResponse` with status 422 and body `{"errors": [{"field": "...", "message": "..."}, ...]}`

## Steps
1. Add imports at the top of `app.py`:
   ```python
   import csv
   import io
   import sqlite3
   import uuid
   from contextlib import asynccontextmanager

   from fastapi import Depends, FastAPI, Response
   from fastapi.exceptions import RequestValidationError
   from fastapi.responses import JSONResponse
   from fastapi.staticfiles import StaticFiles
   ```
2. Implement `POST /submit` above the `StaticFiles` mount:
   ```python
   @app.post("/submit", status_code=201)
   def submit(entry: EggRequest, conn: sqlite3.Connection = Depends(get_db)):
       new_id = str(uuid.uuid4())
       payload = entry.model_dump()
       payload["id"] = new_id
       columns = ", ".join(payload.keys())
       placeholders = ", ".join(f":{k}" for k in payload.keys())
       with conn:
           conn.execute(
               f"INSERT INTO entries ({columns}) VALUES ({placeholders})",
               {k: (v.value if hasattr(v, "value") else v) for k, v in payload.items()},
           )
       return {"id": new_id}
   ```
   The `with conn:` block is a SQLite transaction — auto-commits on success, rolls back on exception. The `(v.value if hasattr(v, 'value') else v)` unwraps Enum members to their string value before inserting.
3. Implement `GET /entries`:
   ```python
   @app.get("/entries")
   def list_entries(conn: sqlite3.Connection = Depends(get_db)):
       rows = conn.execute("SELECT * FROM entries ORDER BY created_at DESC").fetchall()
       return [dict(row) for row in rows]
   ```
   Newest-first ordering is a UX nicety (the most recently submitted row sits at the top of the table); call it out in the README.
4. Implement the CSV export with **both** path decorators on a single function:
   ```python
   @app.get("/export.csv")
   @app.get("/exportcsv")
   def export_csv(conn: sqlite3.Connection = Depends(get_db)):
       rows = conn.execute("SELECT * FROM entries ORDER BY created_at DESC").fetchall()
       buf = io.StringIO()
       fieldnames = (
           ["id", "created_at"] + [f for f in EggRequest.model_fields.keys()]
       )
       writer = csv.DictWriter(buf, fieldnames=fieldnames)
       writer.writeheader()
       for row in rows:
           writer.writerow({k: row[k] for k in fieldnames})
       return Response(
           content=buf.getvalue(),
           media_type="text/csv",
           headers={"Content-Disposition": 'attachment; filename="entries.csv"'},
       )
   ```
   Two decorators on one function is the minimal solution to the spec's `/exportcsv` vs `/export.csv` ambiguity.
5. Add the custom validation handler. Place it just after `app = FastAPI(...)`:
   ```python
   @app.exception_handler(RequestValidationError)
   async def validation_handler(request, exc: RequestValidationError):
       errors = [
           {
               "field": ".".join(str(p) for p in err["loc"][1:]) or err["loc"][0],
               "message": err["msg"],
           }
           for err in exc.errors()
       ]
       return JSONResponse(status_code=422, content={"errors": errors})
   ```
   - `err["loc"][0]` is `"body"` / `"query"` / `"path"`; `err["loc"][1:]` is the field path. Strip the prefix so the frontend can map `field` directly to a form input name.
   - The fallback `or err["loc"][0]` covers the rare case where a top-level error has no field name (e.g., malformed JSON body).
6. Smoke-test with `curl` (server must be running):
   ```bash
   # Happy path
   curl -i -X POST localhost:8000/submit \
     -H 'Content-Type: application/json' \
     -d '{"farm_name":"Acme","contact":"Jane","location":"94110","type":"Organic","size":"Large","grade":"AA","pack":"12ct_carton","quantity_value":12,"quantity_unit":"dozen"}'
   # Expect: HTTP/1.1 201, body {"id":"<uuid>"}

   curl -s localhost:8000/entries | python -m json.tool
   # Expect: a 1-element JSON array containing the row above

   curl -i localhost:8000/export.csv
   curl -i localhost:8000/exportcsv
   # Expect: HTTP/1.1 200, Content-Type: text/csv, body starts with "id,created_at,farm_name,..."

   # Bad path — missing farm_name
   curl -i -X POST localhost:8000/submit \
     -H 'Content-Type: application/json' \
     -d '{"contact":"Jane","location":"94110","type":"Organic","size":"Large","grade":"AA","pack":"12ct_carton","quantity_value":12,"quantity_unit":"dozen"}'
   # Expect: HTTP/1.1 422, body {"errors":[{"field":"farm_name","message":"Field required"}]}

   # Bad path — non-numeric quantity
   curl -i -X POST localhost:8000/submit \
     -H 'Content-Type: application/json' \
     -d '{"farm_name":"Acme","contact":"Jane","location":"94110","type":"Organic","size":"Large","grade":"AA","pack":"12ct_carton","quantity_value":"twelve","quantity_unit":"dozen"}'
   # Expect: HTTP/1.1 422, body {"errors":[{"field":"quantity_value","message":"..."}]}
   ```
7. Stop and restart uvicorn. Hit `GET /entries` again. The previously inserted row should still be there — this is the "data persists after restart" rubric point passing on the backend side.

## Exit criteria
- All four `curl` smoke tests above produce the expected status codes and response bodies.
- `entries.db` accumulates rows; restarting uvicorn does not lose them.
- The `/export.csv` and `/exportcsv` paths return byte-identical responses (one handler, two routes).
- A 422 response body is *always* shaped `{"errors": [...]}` — no `{"detail": [...]}` leaks through (which would mean the handler isn't registered).
- Uvicorn's access log shows `POST /submit -> 201`, `GET /entries -> 200`, `GET /export.csv -> 200`, etc., for every smoke test.

## Walkthrough defense notes
- "Why generate the UUID server-side instead of accepting one from the client?" — The spec literally says `respond { id: "<uuid>" }`; the client gets the ID *back*, not the other way around. Server-side also prevents a client from picking colliding IDs.
- "What does `with conn:` do?" — SQLite context-manager protocol: commits the transaction on clean exit, rolls back on exception. One line of code = atomic insert.
- "Why two decorators on one function?" — The spec writes both `/exportcsv` and `/export.csv`. Implementing one handler and registering both paths is two extra lines and removes any chance of a point loss for picking the "wrong" spelling.
- "Why `error['loc'][1:]`?" — Pydantic returns `("body", "farm_name")` for body field errors; we drop `"body"` so the frontend's field-mapping logic only sees `"farm_name"`.
- "Why `Content-Disposition: attachment`?" — Tells the browser to download the file rather than render it inline. `filename="entries.csv"` becomes the default save name.

## Out of scope for this phase
- **No frontend changes.** Phase 4 wires the form to these endpoints and renders the new error shape inline.
- **No tests.** Phase 5.
- **No pagination, search, or filtering on `/entries`** — AGENTS.md §5 vetoes.
- **No streaming the CSV.** `io.StringIO` in memory is fine for a take-home with ~10s of rows; streaming via `StreamingResponse` would be over-engineering.
- **No DELETE / PUT endpoints.** Spec doesn't ask for them.
- **No `Optional` upgrade for the date fields** — `available_start` and `available_end` stay as `str | None`. Phase 6 documents this trade-off.
