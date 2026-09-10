"""Lightweight SQLite verification history. No uploaded images are stored — only results."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_SCHEMA = """
CREATE TABLE IF NOT EXISTS verifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    user_id TEXT,
    food_category TEXT,
    food_confidence REAL,
    authenticity_result TEXT,
    ai_probability REAL,
    fusion_score REAL,
    final_decision TEXT NOT NULL
);
"""


@dataclass
class HistoryRecord:
    id: int
    timestamp: str
    user_id: Optional[str]
    food_category: Optional[str]
    food_confidence: Optional[float]
    authenticity_result: Optional[str]
    ai_probability: Optional[float]
    fusion_score: Optional[float]
    final_decision: str


@contextmanager
def _connect(db_path: Path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute(_SCHEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()


def add_record(
    db_path: Path,
    *,
    user_id: Optional[str],
    food_category: Optional[str],
    food_confidence: Optional[float],
    authenticity_result: Optional[str],
    ai_probability: Optional[float],
    fusion_score: Optional[float],
    final_decision: str,
) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            """INSERT INTO verifications
               (timestamp, user_id, food_category, food_confidence,
                authenticity_result, ai_probability, fusion_score, final_decision)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
                user_id, food_category, food_confidence,
                authenticity_result, ai_probability, fusion_score, final_decision,
            ),
        )


def list_records(
    db_path: Path, *, user_id: Optional[str] = None, search: Optional[str] = None, limit: int = 200
) -> list[HistoryRecord]:
    query = "SELECT * FROM verifications"
    clauses, params = [], []
    if user_id:
        clauses.append("user_id = ?")
        params.append(user_id)
    if search:
        clauses.append("(food_category LIKE ? OR final_decision LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    with _connect(db_path) as conn:
        rows = conn.execute(query, params).fetchall()
    return [HistoryRecord(**dict(row)) for row in rows]
