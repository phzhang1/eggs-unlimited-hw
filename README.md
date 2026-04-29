# Eggs Unlimited — Request Eggs Form

A small local FastAPI + SQLite web app for submitting and listing egg supply requests from shops.

---

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```

Dependencies are pinned in `requirements.txt` for reproducible installs.

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Renders the request form |
| `POST` | `/submit` | Saves one record; responds `{ "id": "<uuid>" }` |
| `GET` | `/entries` | Returns all records as JSON |
| `GET` | `/export.csv` | Downloads all records as a CSV file |
| `GET` | `/exportcsv` | Alias for `/export.csv` (same handler, both paths registered) |
| `GET` | `/healthz` | Returns `200 OK` |

---

## Architecture

```mermaid
flowchart LR
    Browser -->|POST /submit\nGET /entries| FastAPI
    FastAPI -->|sqlite3| SQLite[(entries.db)]
    FastAPI -->|StaticFiles| Browser
```

---

## Form Fields & Validation

Fields marked **required** must be present in every submission. Enum values are the only accepted strings for those fields.

| Field | Required | Type / Constraints |
|-------|----------|--------------------|
| `farm_name` | **yes** | string |
| `contact` | **yes** | string |
| `phone_email` | no | string |
| `location` | **yes** | string (ZIP or city) |
| `type` | **yes** | enum: `Conventional`, `CageFree`, `FreeRange`, `Organic` |
| `size` | **yes** | enum: `Medium`, `Large`, `XLarge`, `Jumbo` |
| `grade` | **yes** | enum: `AA`, `A`, `B` |
| `pack` | **yes** | enum: `12ct_carton`, `18ct_carton`, `24ct_tray`, `30dozen_case` |
| `quantity_value` | **yes** | numeric (positive number) |
| `quantity_unit` | **yes** | string (e.g., `dozen`, `case`) |
| `price_per_dozen` | no | numeric |
| `available_start` | no | date string |
| `available_end` | no | date string |
| `notes` | no | string |

Validation is enforced at three layers: HTML5 `required` attributes (UX), Pydantic at the API boundary (types + required), and SQLite `CHECK` constraints on enum columns (defense-in-depth).

---

## Running the Tests

<!-- FILL IN PHASE 5 -->

```bash
pytest -v
```

---

## Decisions & Trade-offs

Phase 2 Choices (data model + DB layer):

- **Pydantic model design (flat vs nested)**: I used a flat `EggRequest` model because the fields are simple attributes of a single record, and do not form reusuable sub-objects. Nesting would add unnecessary mapping complexity.
- **Enum-backed fields**: I used enums to centralize allowed values in named types (`EggType`, `EggSize`, etc.), which keeps validation rules explicit and reusable in code vs. repeating raw string lists inline. I also mirror the same set in SQLite `CHECK` constraints for defense-in-depth.
- **Database schema shape**: I used one denormalized `entries` table since the app stores a single request record type with small and fixed enum sets. Normalizing into lookup tables would add joins and extra query logic with little practical benefits at this scale.
- **Startup initialization (`lifespan`)**: I run `init_db()` in FastAPI's lifespan startup so a fresh clone creates the table automatically before serving requests.
- **SQLite connection lifecycle**: After startup, each request opens its own SQLite connection and closes it in a dependency `finally` block, which prevents leaks and keeps runtime behavior reliable.

Phase 3 Choices (endpoints and validation)
- **CSV route ambiguity (`/export.csv` vs `/exportcsv`)**: Register both paths on one handler to match spec wording differences.
- **Friendly validation error**: Added a customer `RequestValidationError` handler returning `{"errors":[{"field","message}]}` so frontend can map errors directly to inputs instead of FastAPI's default `detail` structure.
- **CSV generation approach**: Used `csv.DictWriter` + `io.StringIO` in-memory because dataset size is small; streaming would add complexity with little value for the scope of the assignment.
- **Entries ordering**: `Get /entries` returns newest first (`ORDER BY created_at DESC`) so recent submissions appear at top of the UI table.
- **Server-side UUID generation in `POST /submit`**: Keeps ID creation authoritative on backend and matches spec reponse `{"id": "<uuid>"}`.
<!-- ---

## What I'd Add With More Time

- Pagination on `/entries` (no filtering in scope, but the list will grow)
- CSRF protection on the form
- Structured logging (JSON lines, request-id header)
- A small Playwright end-to-end test alongside the pytest unit tests
- A `DELETE /entries/{id}` endpoint
- Postgres + connection pool if the app ever needed to handle more than one concurrent user

--- -->

<!-- ## Walkthrough Cheat Sheet

See [AGENTS.md §8](AGENTS.md#8-walkthrough-defense-cheat-sheet) for likely reviewer questions and short, defendable answers.

> Note: If `AGENTS.md` is not shipped in the final repo, inline the cheat sheet here during Phase 6. -->

---

<!--
BRAINSTORM — fill this in before Phase 1; delete or keep private

1. What's the one thing about this project I'm least sure I can defend in 30 seconds?
   [your answer here]

2. Which of the 14 §6 decisions feel arbitrary to me, and what would I prefer to do instead?
   [your answer here]

3. Which form field do I expect to be hardest to validate cleanly?
   [your answer here]
-->
