"""Seed normalized Postgres table bench_reviews for doc-vs-rel benchmarks."""

from __future__ import annotations

import os
import random
import uuid

import psycopg


TOTAL = int(os.getenv("TOTAL", "500_000"))
FILMS = int(os.getenv("FILMS", "5_000"))

PG_DSN = os.getenv(
    "PG_DSN",
    "postgresql://bench:bench@postgres:5432/bench",
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS bench_reviews (
    id UUID PRIMARY KEY,
    film_id UUID NOT NULL,
    user_id UUID NOT NULL,
    text TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    hot INT NOT NULL,
    up_cnt INT NOT NULL DEFAULT 0,
    down_cnt INT NOT NULL DEFAULT 0,
    badge TEXT NULL
);

CREATE INDEX IF NOT EXISTS idx_br_film_hot_created
    ON bench_reviews (film_id, hot DESC, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_br_badge
    ON bench_reviews (badge);
"""


def main() -> None:
    """Populate bench_reviews with synthetic rows across many films."""
    with psycopg.connect(PG_DSN, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(SCHEMA)
            cur.execute("TRUNCATE bench_reviews")

            rows: list[tuple] = []

            import datetime  # local import to keep global namespace minimal

            now = datetime.datetime.now(tz=datetime.timezone.utc)

            # helper to keep approximately FILMS distinct film_ids
            last_film_id: uuid.UUID | None = None
            step = TOTAL // FILMS or 1

            for i in range(TOTAL):
                if i % step == 0 or last_film_id is None:
                    last_film_id = uuid.uuid4()

                film_id = last_film_id
                badge = (
                    random.choice(["critic", "verified"])
                    if random.random() < 0.3
                    else None
                )

                created_at = now - datetime.timedelta(
                    seconds=random.randint(0, 3600 * 24 * 7),
                )

                rows.append(
                    (
                        uuid.uuid4(),         # id
                        film_id,              # film_id
                        uuid.uuid4(),         # user_id
                        "lorem",              # text
                        created_at,           # created_at
                        random.randint(0, 1000),  # hot
                        0,                    # up_cnt
                        0,                    # down_cnt
                        badge,                # badge
                    ),
                )

                if len(rows) == 50_000:
                    cur.executemany(
                        "INSERT INTO bench_reviews "
                        "(id, film_id, user_id, text, created_at, hot, "
                        " up_cnt, down_cnt, badge) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        rows,
                    )
                    rows.clear()

            if rows:
                cur.executemany(
                    "INSERT INTO bench_reviews "
                    "(id, film_id, user_id, text, created_at, hot, "
                    " up_cnt, down_cnt, badge) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    rows,
                )

    print("pg bench_reviews seeded")


if __name__ == "__main__":
    main()
