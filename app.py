import sqlite3
import uuid
from contextlib import asynccontextmanager
from enum import Enum

from fastapi import Depends, FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


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
    farm_name:      str
    contact:        str       # contact person's name
    location:       str       # ZIP code or city
    type:           EggType
    size:           EggSize
    grade:          EggGrade
    pack:           EggPack
    quantity_value: float     # Pydantic rejects non-numeric input
    quantity_unit:  str      

    # Optional fields (spec does not list these as required)
    phone_email:     str | None   = None  # phone or email (separate from contact name)
    price_per_dozen: float | None = None  # numeric if provided
    available_start: str | None   = None  # plain string (spec doesn't require date parsing)
    available_end:   str | None   = None
    notes:           str | None   = None


# Database: creates table with the constraints defined in the enums above

DB_PATH = "entries.db"


def init_db() -> None:
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
    conn.close()

# Lifespan: runs once at startup and prevents manual database initialization

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Eggs Unlimited", lifespan=lifespan)


# Routes

@app.get("/healthz")
def healthz():
    return {"status": "ok"}



# DB dependency: one connection per request to avoid connection leaks

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


# Keep at the end of the file to avoid catching API requests before routes are registered.
app.mount("/", StaticFiles(directory="static", html=True), name="static")
