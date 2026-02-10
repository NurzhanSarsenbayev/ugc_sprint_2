"""
Seed Mongo collection `bench_reviews` for TopN-many-films benchmarks.

This dataset is intentionally different from `seed_reviews.py`:
- `seed_reviews.py` is a single-film workload (good for "top-tail" scenario).
- this seeder generates many film_id values (good for TopN across many films).

The benchmark runner `scripts/bench/runs/topn_many_films.py` uses:
- collection: bench_reviews
- fields: film_id, created_at, votes_counters.up, votes (tail)
"""

from __future__ import annotations

import asyncio
import os
import random
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient

MONGO_DSN = os.getenv(
    "MONGO_DSN",
    "mongodb://mongo:27017/engagement_bench?replicaSet=rs0",
)

TOTAL = int(os.getenv("TOTAL", "300000"))          # total reviews docs
FILMS = int(os.getenv("FILMS", "5000"))            # distinct film_id count
BATCH = int(os.getenv("BATCH", "1000"))            # insert_many batch size

MAX_VOTES = int(os.getenv("MAX_VOTES", "200"))
TAIL_MAX = int(os.getenv("TAIL_MAX", "20"))
USERS_POOL = int(os.getenv("USERS_POOL", "200000"))


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def make_film_pool(n: int) -> list[str]:
    # string UUIDs to match existing dataset style
    return [str(uuid.uuid4()) for _ in range(n)]


def make_user_pool(n: int) -> list[str]:
    # keep a pool to avoid generating billions of uuids in heavy runs
    # (still random enough for benchmarks)
    return [str(uuid.uuid4()) for _ in range(n)]


def build_votes_tail(tail_len: int, user_pool: list[str]) -> list[dict[str, Any]]:
    votes: list[dict[str, Any]] = []
    for _ in range(tail_len):
        votes.append(
            {
                "user_id": random.choice(user_pool),
                "value": random.choice(["up", "down"]),
                "ts": now_utc() - timedelta(seconds=random.randint(0, 60 * 60 * 24)),
            },
        )
    return votes


async def main() -> None:
    cli = AsyncIOMotorClient(MONGO_DSN)
    db = cli.get_default_database()
    col = db["bench_reviews"]

    # deterministic + benchmark-friendly: start fresh
    await col.drop()

    # indexes used by TopN pipeline
    await col.create_index(
        [("film_id", 1), ("votes_counters.up", -1), ("created_at", -1)],
    )
    await col.create_index([("created_at", -1)])

    film_ids = make_film_pool(FILMS)
    # users pool is kept in-memory; if you want fully unique users,
    # set USERS_POOL very high or remove pool usage (slower).
    user_ids = make_user_pool(min(USERS_POOL, 200_000))

    t0 = time.time()
    bulk: list[dict[str, Any]] = []

    for i in range(TOTAL):
        film_id = random.choice(film_ids)
        user_id = random.choice(user_ids)

        created = now_utc() - timedelta(seconds=random.randint(0, 60 * 60 * 24))

        up = random.randint(0, MAX_VOTES)
        down = random.randint(0, MAX_VOTES // 2)

        # votes tail length: bounded and proportional-ish to total votes
        tail_len = random.randint(0, min(TAIL_MAX, up + down))
        votes_tail = build_votes_tail(tail_len, user_ids)

        bulk.append(
            {
                "_id": str(uuid.uuid4()),
                "film_id": film_id,
                "user_id": user_id,
                "text": f"Review {i}",
                "created_at": created,
                "votes": votes_tail,
                "votes_counters": {"up": up, "down": down},
            },
        )

        if len(bulk) >= BATCH:
            await col.insert_many(bulk, ordered=False)
            bulk.clear()

    if bulk:
        await col.insert_many(bulk, ordered=False)

    dur = time.time() - t0
    distinct_films = len(await col.distinct("film_id"))
    print(
        "[mongo] seeded bench_reviews total={} films={} distinct={} in {:.1f}s".format(
            TOTAL,
            FILMS,
            distinct_films,
            dur,
        ),
    )

    cli.close()


if __name__ == "__main__":
    asyncio.run(main())
