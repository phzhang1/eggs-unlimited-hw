import csv
import io
import sqlite3
import uuid
from contextlib import asynccontextmanager
from enum import Enum

from fastapi import Depends, FastAPI, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


# Enums: a controlled list of allowed values (prevent bad data and validate automatically)

class EggType(str, Enum):
    conventional = "Conventional"
    cage_free    = "CageFree"
    free_range   = "FreeRange"
    organic      = "Organic"


class EggSize(str, Enum):
    medium = "Medium"
    large  = "Large"
    xlarge = "XLarge"
    jumbo  = "Jumbo"


class EggGrade(str, Enum):
    aa = "AA"
    a  = "A"
    b  = "B"


class EggPack(str, Enum):
    carton_12   = "12ct_carton"
    carton_18   = "18ct_carton"
    tray_24     = "24ct_tray"
    case_30doz  = "30dozen_case"



# Pydantic model: separate required and optional fields and validate data types automatically

class EggRequest(BaseModel):
    # Required fields (no default means Pydantic rejects missing values)
    farm_name:      str = Field(min_length=1)
    contact:        str = Field(min_length=1)  # contact person's name
    location:       str = Field(min_length=1)  # ZIP code or city
    type:           EggType
    size:           EggSize
    grade:          EggGrade
    pack:           EggPack
    quantity_value: float                      # Pydantic rejects non-numeric input
    quantity_unit:  str = Field(min_length=1)

    # Optional fields (spec does not list these as required)
    phone_email:     str | None   = None  # phone or email (separate from contact name)
    price_per_dozen: float | None = None  # numeric if provided
    available_start: str | None   = None  # plain string (spec doesn't require date parsing)
    available_end:   str | None   = None
    notes:           str | None   = None


# Database: creates table with the constraints defined in the enums above

DB_PATH = "entries.db"


def init_db(conn: sqlite3.Connection | None = None) -> None:
    # accept temporary connection to allow testing
    own_conn = conn is None
    if own_conn:
        conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id               TEXT PRIMARY KEY,
            farm_name        TEXT NOT NULL,
            contact          TEXT NOT NULL,
            phone_email      TEXT,
            location         TEXT NOT NULL,
            type             TEXT NOT NULL CHECK (type IN ('Conventional','CageFree','FreeRange','Organic')),
            size             TEXT NOT NULL CHECK (size IN ('Medium','Large','XLarge','Jumbo')),
            grade            TEXT NOT NULL CHECK (grade IN ('AA','A','B')),
            pack             TEXT NOT NULL CHECK (pack IN ('12ct_carton','18ct_carton','24ct_tray','30dozen_case')),
            quantity_value   REAL NOT NULL,
            quantity_unit    TEXT NOT NULL,
            price_per_dozen  REAL,
            available_start  TEXT,
            available_end    TEXT,
            notes            TEXT,
            created_at       TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    if own_conn:
        conn.close()

# Lifespan: runs once at startup and prevents manual database initialization

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Eggs Unlimited", lifespan=lifespan)


# DB dependency: one connection per request to avoid connection leaks.
# Defined before routes so the name is in scope when route default args are evaluated.
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


# Reformat validation errors into clean UX inline errors
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


# Routes

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

# creates a new entry in the database
@app.post("/submit", status_code=201)
def submit(entry: EggRequest, conn: sqlite3.Connection = Depends(get_db)):
    new_id = str(uuid.uuid4())
    payload = entry.model_dump()
    payload["id"] = new_id
    columns = ", ".join(payload.keys())
    placeholders = ", ".join(f":{k}" for k in payload.keys())
    # wraps insert into transaction to prevent partial writes if the database is corrupted
    with conn:
        conn.execute(
            f"INSERT INTO entries ({columns}) VALUES ({placeholders})",
            {k: (v.value if hasattr(v, "value") else v) for k, v in payload.items()},
        )
    return {"id": new_id}

# reads all entries from the database
@app.get("/entries")
def list_entries(conn: sqlite3.Connection = Depends(get_db)):
    rows = conn.execute("SELECT * FROM entries ORDER BY created_at DESC").fetchall()
    return [dict(row) for row in rows]


# two gets for same endpoint: handles spellings from spec (not POST because it reads and returns data, no action)
@app.get("/export.csv")
@app.get("/exportcsv")
def export_csv(conn: sqlite3.Connection = Depends(get_db)):
    rows = conn.execute("SELECT * FROM entries ORDER BY created_at DESC").fetchall()
    buf = io.StringIO()
    fieldnames = ["id", "created_at"] + list(EggRequest.model_fields.keys())
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow({k: row[k] for k in fieldnames})
    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="entries.csv"'},
    )


# Keep at the end of the file to avoid catching API requests before routes are registered.
app.mount("/", StaticFiles(directory="static", html=True), name="static")
