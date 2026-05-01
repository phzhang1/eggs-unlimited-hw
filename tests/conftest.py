import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app as app_module


@pytest.fixture()
def client(tmp_path: Path):
    """A TestClient backed by a fresh, isolated SQLite file for each test.

    Why dependency_overrides: FastAPI's documented way to swap a Depends()
    target during tests without touching production code. Each test gets its
    own tmp_path so tests cannot leak state into each other.

    Why tmp_path instead of :memory:: SQLite :memory: databases are
    per-connection. With our per-request connection model, each request would
    see a fresh empty DB. A temp file behaves identically to the production DB
    but is isolated per test.
    """
    db_path = tmp_path / "test_entries.db"

    def override_get_db():
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    # Bootstrap the schema against the test DB before any request runs.
    init_conn = sqlite3.connect(db_path)
    try:
        app_module.init_db(init_conn)
    finally:
        init_conn.close()

    app_module.app.dependency_overrides[app_module.get_db] = override_get_db
    try:
        yield TestClient(app_module.app)
    finally:
        app_module.app.dependency_overrides.clear()
