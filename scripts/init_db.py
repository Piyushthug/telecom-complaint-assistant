"""One-off script: load data/complaint_history.csv into a local SQLite database.

Run with:
    python scripts/init_db.py
"""
import csv
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend import config

CSV_PATH = config.DATA_DIR / "complaint_history.csv"


def main() -> None:
    connection = sqlite3.connect(config.SQLITE_DB_PATH)
    try:
        connection.execute("DROP TABLE IF EXISTS complaint_history")
        connection.execute(
            """
            CREATE TABLE complaint_history (
                complaint_id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL,
                category TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                resolution_time_hours REAL
            )
            """
        )

        with open(CSV_PATH, newline="", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            rows = [
                (
                    row["complaint_id"],
                    row["customer_id"],
                    row["category"],
                    row["status"],
                    row["created_at"],
                    float(row["resolution_time_hours"]) if row["resolution_time_hours"] else None,
                )
                for row in reader
            ]

        connection.executemany(
            """
            INSERT INTO complaint_history
            (complaint_id, customer_id, category, status, created_at, resolution_time_hours)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        connection.commit()
        print(f"Loaded {len(rows)} rows into {config.SQLITE_DB_PATH}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
