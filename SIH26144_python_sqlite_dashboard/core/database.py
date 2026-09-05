import sqlite3
from pathlib import Path
from typing import Iterable


def connect(db_path: Path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS calibration_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                method TEXT,
                frequency_hz REAL,
                input_pressure_pa REAL,
                output_voltage_mv REAL,
                measured_sensitivity REAL,
                r_squared REAL,
                leak_tau_s REAL,
                notes TEXT
            )
        """)
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


def save_calibration_record(db_path: Path, record: dict):
    with connect(db_path) as c:
        c.execute("""
            INSERT INTO calibration_records 
            (timestamp, method, frequency_hz, input_pressure_pa, output_voltage_mv, measured_sensitivity, r_squared, leak_tau_s, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.get("timestamp"),
            record.get("method"),
            record.get("frequency_hz"),
            record.get("input_pressure_pa"),
            record.get("output_voltage_mv"),
            record.get("measured_sensitivity"),
            record.get("r_squared"),
            record.get("leak_tau_s"),
            record.get("notes", "")
        ))


def read_calibration_records(db_path: Path, method: str = None, limit: int = 50):
    with connect(db_path) as c:
        if method:
            rows = c.execute(
                "SELECT * FROM calibration_records WHERE method = ? ORDER BY id DESC LIMIT ?",
                (method, limit),
            ).fetchall()
        else:
            rows = c.execute(
                "SELECT * FROM calibration_records ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
    return [dict(r) for r in rows]

