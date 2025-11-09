"""Seed reviews dataset for both MongoDB and Postgres (single FILM_ID)."""

from __future__ import annotations

import asyncio
import os
import random
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import List

from motor.motor_asyncio import AsyncIOMotorClient
import psycopg


# --------------------------- settings ----------------------------------------

MONGO_DSN = os.getenv(
    "MONGO_DSN",
    "mongodb://mongo:27017/engagement_bench?replicaSet=rs0",
)
PG_DSN = os.getenv(
    "PG_DSN",
    "postgresql://bench:bench@postgres:5432/bench",
)

N_REVIEWS = int(os.getenv("N_REVIEWS", "100000"))
MAX_VOTES = int(os.getenv("MAX_VOTES", "200"))
USERS_POOL = int(os.getenv("USERS_POOL", "200000"))
FILM_ID = os.getenv("FILM_ID", str(uuid.uuid4()))
TAIL_MAX = int(os.getenv("TAIL_MAX", "20"))


# --------------------------- helpers -----------------------------------------


def now_utc() -> datetime:
    """Current UTC datetime."""
    return datetime.now(timezone.utc)


# --------------------------- Postgres DDL ------------------------------------


PG_SCHEMA = """
CREATE TABLE IF NOT EXISTS reviews (
    id          UUID PRIMARY KEY,
    film_id     UUID NOT NULL,
    user_id     UUID NOT NULL,
    text        TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL,
    votes_up    INTEGER NOT NULL DEFAULT 0,
    votes_down  INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_reviews_film_top
  ON reviews (film_id, votes_up DESC, created_at DESC);

CREATE TABLE IF NOT EXISTS review_votes (
    review_id   UUID NOT NULL,
    user_id     UUID NOT NULL,
    value       TEXT NOT NULL CHECK (value IN ('up','down')),
    ts          TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (review_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_review_votes_review_ts
  ON review_votes (review_id, ts DESC);
"""


# --------------------------- Mongo seed --------------------------------------


async def seed_mongo() -> None:
    """Seed MongoDB collection bench_reviews for a given FILM_ID."""
    mongo = AsyncIOMotorClient(MONGO_DSN)
    db = mongo.get_default_database()
    reviews = db["bench_reviews"]

    # indexes
    await reviews.create_index(
        [("film_id", 1), ("votes_counters.up", -1), ("created_at", -1)],
    )
    await reviews.create_index([("created_at", -1)])

    # cleanup for target film
    await reviews.delete_many({"film_id": FILM_ID})

    start = time.time()
    bulk: List[dict] = []

    for i in range(N_REVIEWS):
        review_id = str(uuid.uuid4())
        created = now_utc() - timedelta(
            seconds=random.randint(0, 60 * 60 * 24),
        )
        up = random.randint(0, MAX_VOTES)
        down = random.randint(0, MAX_VOTES // 2)

        tail = random.randint(0, min(TAIL_MAX, up + down))
        votes: List[dict] = []
        for _ in range(tail):
            votes.append(
                {
                    "user_id": str(uuid.uuid4()),
                    "value": random.choice(["up", "down"]),
                    "ts": now_utc()
                    - timedelta(seconds=random.randint(0, 60 * 60 * 24)),
                },
            )

        bulk.append(
            {
                "_id": review_id,
                "film_id": FILM_ID,
                "user_id": str(uuid.uuid4()),
                "text": f"Review {i}",
                "created_at": created,
                "votes": votes,
                "votes_counters": {"up": up, "down": down},
            },
        )

        if len(bulk) == 1000:
            await reviews.insert_many(bulk)
            bulk.clear()

    if bulk:
        await reviews.insert_many(bulk)

    dur = time.time() - start
    print(
        "[mongo] seeded reviews={} film={} in {:.1f}s".format(
            N_REVIEWS,
            FILM_ID,
            dur,
        ),
    )
    mongo.close()


# --------------------------- Postgres seed -----------------------------------


def seed_pg() -> None:
    """Seed Postgres tables reviews and review_votes for a given FILM_ID."""
    with psycopg.connect(PG_DSN, autocommit=True) as conn:
        # ensure schema
        with conn.cursor() as cur:
            cur.execute(PG_SCHEMA)

        # cleanup for target film
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM review_votes
                USING reviews r
                WHERE review_votes.review_id = r.id AND r.film_id = %s
                """,
                (FILM_ID,),
            )
            cur.execute("DELETE FROM reviews WHERE film_id = %s", (FILM_ID,))

        start = time.time()
        reviews_rows: List[tuple] = []
        votes_rows: List[tuple] = []

        for i in range(N_REVIEWS):
            rid = uuid.uuid4()
            created = now_utc() - timedelta(
                seconds=random.randint(0, 60 * 60 * 24),
            )
            up = random.randint(0, MAX_VOTES)
            down = random.randint(0, MAX_VOTES // 2)

            reviews_rows.append(
                (
                    rid,
                    FILM_ID,
                    uuid.uuid4(),
                    f"Review {i}",
                    created,
                    up,
                    down,
                ),
            )

            # tail of last votes 0..5 for LATERAL usage
            for _ in range(random.randint(0, 5)):
                votes_rows.append(
                    (
                        rid,
                        uuid.uuid4(),
                        random.choice(["up", "down"]),
                        now_utc()
                        - timedelta(seconds=random.randint(0, 60 * 60 * 24)),
                    ),
                )

            if len(reviews_rows) >= 5000:
                with conn.cursor() as cur:
                    cur.executemany(
                        """
                        INSERT INTO reviews
                        (id,
                         film_id,
                         user_id,
                         text,
                         created_at,
                         votes_up,
                         votes_down)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        reviews_rows,
                    )
                reviews_rows.clear()

            if len(votes_rows) >= 10000:
                with conn.cursor() as cur:
                    cur.executemany(
                        """
                        INSERT INTO review_votes
                        (review_id, user_id, value, ts)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                        """,
                        votes_rows,
                    )
                votes_rows.clear()

        if reviews_rows:
            with conn.cursor() as cur:
                cur.executemany(
                    """
                    INSERT INTO reviews
                    (id,
                     film_id,
                     user_id,
                     text,
                     created_at,
                     votes_up,
                     votes_down)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    reviews_rows,
                )

        if votes_rows:
            with conn.cursor() as cur:
                cur.executemany(
                    """
                    INSERT INTO review_votes
                    (review_id, user_id, value, ts)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    votes_rows,
                )

        dur = time.time() - start
        print(
            "[pg]    seeded reviews={} film={} in {:.1f}s".format(
                N_REVIEWS,
                FILM_ID,
                dur,
            ),
        )


# --------------------------- entrypoint --------------------------------------


async def main() -> None:
    """Run seeds for Mongo and Postgres."""
    print(f"FILM_ID={FILM_ID}")
    await seed_mongo()
    seed_pg()


if __name__ == "__main__":
    asyncio.run(main())
