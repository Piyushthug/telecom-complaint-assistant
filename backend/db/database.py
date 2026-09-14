"""SQLite-backed complaint history: used for repeated-complaint detection."""
import sqlite3
from contextlib import contextmanager
from typing import Iterator

from backend import config


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(config.SQLITE_DB_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()


def get_customer_history(customer_id: str) -> list:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT complaint_id, category, status, created_at, resolution_time_hours
            FROM complaint_history
            WHERE customer_id = ?
            ORDER BY created_at DESC
            """,
            (customer_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def count_recent_same_category(customer_id: str, category: str) -> int:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM complaint_history
            WHERE customer_id = ? AND category = ?
            """,
            (customer_id, category),
        ).fetchone()
    return row["count"] if row else 0
