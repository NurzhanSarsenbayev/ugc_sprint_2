"""Seed Postgres 'ratings' table using COPY from temporary CSV files."""

from __future__ import annotations

import csv
import os
import random
import tempfile
import time
import uuid

import psycopg
from psycopg import sql


PG_DSN = os.getenv(
    "PG_DSN",
    "postgresql://bench:bench@localhost:5432/bench",
)
TOTAL = int(os.getenv("TOTAL", "1000000"))
CSV_BATCH = int(os.getenv("CSV_BATCH", "100000"))  # rows per temp CSV file


def ensure_schema(conn: psycopg.Connection) -> None:
    """Create ratings table and indexes if not exist."""
    ddl = """
    CREATE TABLE IF NOT EXISTS ratings (
      film_id  UUID NOT NULL,
      user_id  UUID NOT NULL,
      score    SMALLINT NOT NULL CHECK (score BETWEEN 1 AND 10),
      PRIMARY KEY (film_id, user_id)
    );
    CREATE INDEX IF NOT EXISTS idx_ratings_user ON ratings(user_id);
    """
    with conn.cursor() as cur:
        cur.execute(ddl)
    conn.commit()


def copy_csv(conn: psycopg.Connection, path: str) -> None:
    """COPY data from CSV file into ratings."""
    copy_stmt = (
        "COPY ratings (film_id, user_id, score) "
        "FROM STDIN WITH (FORMAT CSV)"
    )
    with conn.cursor() as cur, open(path, "r", newline="") as f:
        cur.copy(sql.SQL(copy_stmt), f)
    conn.commit()


def main() -> None:
    """Generate CSV chunks and bulk load into Postgres."""
    t0 = time.time()
    with psycopg.connect(PG_DSN) as conn:
        ensure_schema(conn)
        left = TOTAL
        while left > 0:
            n = min(CSV_BATCH, left)
            with tempfile.NamedTemporaryFile(
                "w",
                delete=False,
                newline="",
            ) as tmp:
                writer = csv.writer(tmp)
                for _ in range(n):
                    writer.writerow(
                        [
                            str(uuid.uuid4()),
                            str(uuid.uuid4()),
                            random.randint(1, 10),
                        ],
                    )
                path = tmp.name
            copy_csv(conn, path)
            left -= n

    dt = time.time() - t0
    rate = int(TOTAL / dt) if dt > 0 else 0
    print(f"[pg] inserted={TOTAL} in {dt:.1f}s ({rate} rows/s)")


if __name__ == "__main__":
    main()
