import sqlite3
from pathlib import Path
from typing import Iterable


def connect(db_path: Path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def source_info(db_path: Path):
    with connect(db_path) as c:
        first = c.execute("SELECT MIN(id) AS x FROM samples").fetchone()["x"]
        last = c.execute("SELECT MAX(id) AS x FROM samples").fetchone()["x"]
        count = c.execute("SELECT COUNT(*) AS n FROM samples").fetchone()["n"]
    return {"first_id": first, "last_id": last, "count": count}


def read_samples(db_path: Path, start_id: int, limit: int):
    with connect(db_path) as c:
        rows = c.execute(
            "SELECT * FROM samples WHERE id >= ? ORDER BY id LIMIT ?",
            (start_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def read_first_samples(db_path: Path, limit: int):
    with connect(db_path) as c:
        rows = c.execute(
            "SELECT * FROM samples ORDER BY id LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def read_events(db_path: Path, limit: int = 100):
    with connect(db_path) as c:
        rows = c.execute(
            "SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]
