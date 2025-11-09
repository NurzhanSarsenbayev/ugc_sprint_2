"""Benchmark: document (Mongo) vs relational (Postgres) review flows."""

from __future__ import annotations

import asyncio
import os
import random
import time
import uuid

from motor.motor_asyncio import AsyncIOMotorClient
import psycopg


OPS = int(os.getenv("OPS", "20000"))
CONCURRENCY = int(os.getenv("CONCURRENCY", "20"))
TOPN = int(os.getenv("TOPN", "20"))
K_LAST = int(os.getenv("K_LAST", "20"))

MONGO_DSN = os.getenv(
    "MONGO_DSN",
    (
        "mongodb://mongo:27017/"
        "engagement_bench?replicaSet=rs0"
    ),
)
PG_DSN = os.getenv(
    "PG_DSN",
    "postgresql://bench:bench@postgres:5432/bench",
)


# --- Mongo ops ---------------------------------------------------------------


async def mongo_toggle_and_query(col, film_id: str, user_id: str):
    """Toggle vote and fetch top-N with last K votes slice."""
    vote = random.choice([("up", 1), ("down", -1)])
    inc = {"counters.up": 1} if vote[0] == "up" else {"counters.down": 1}

    await col.update_one(
        {"film_id": film_id},
        {
            "$inc": inc,
            "$push": {
                "last_votes": {
                    "$each": [{"user": user_id, "v": vote[0]}],
                    "$slice": -K_LAST,
                },
            },
        },
    )

    pipeline = [
        {
            "$match": {
                "film_id": film_id,
                "attrs.badge": {"$in": ["critic", "verified"]},
            },
        },
        {"$sort": {"hot": -1, "created_at": -1}},
        {"$limit": TOPN},
        {
            "$project": {
                "film_id": 1,
                "hot": 1,
                "created_at": 1,
                "counters": 1,
                "last_votes": 1,
            },
        },
    ]
    return await col.aggregate(pipeline).to_list(length=TOPN)


# --- PG ops (approximation) --------------------------------------------------


def pg_toggle_and_query(cur, film_id: str, user_id: str):
    """Increment counters and fetch top-N (no last-votes array)."""
    if random.random() < 0.5:
        cur.execute(
            "UPDATE bench_reviews SET up_cnt = up_cnt + 1 WHERE film_id = %s",
            (film_id,),
        )
    else:
        cur.execute(
            "UPDATE bench_reviews "
            "SET down_cnt = down_cnt + 1 WHERE film_id = %s",
            (film_id,),
        )

    cur.execute(
        """
        SELECT film_id, hot, created_at, up_cnt, down_cnt
        FROM bench_reviews
        WHERE film_id = %s AND badge IN ('critic','verified')
        ORDER BY hot DESC, created_at DESC
        LIMIT %s
        """,
        (film_id, TOPN),
    )
    return cur.fetchall()


# --- Runner ------------------------------------------------------------------


async def run() -> None:
    """Run both scenarios and print p50/p95 timings."""
    # Prepare clients
    mongo_client = AsyncIOMotorClient(MONGO_DSN)
    mongo_db = mongo_client.get_default_database()
    mongo_col = mongo_db["reviews_doc"]

    film_ids = [
        d["film_id"]
        async for d in mongo_col.find({}, {"film_id": 1}).limit(10_000)
    ]
    assert film_ids, "seed Mongo first"

    pg_conn = psycopg.connect(PG_DSN, autocommit=True)
    pg_cur = pg_conn.cursor()
    pg_cur.execute("SELECT film_id FROM bench_reviews LIMIT 10000")
    pg_films = [row[0] for row in pg_cur.fetchall()]

    async def worker_m() -> list[float]:
        latencies: list[float] = []
        iters = OPS // CONCURRENCY
        for _ in range(iters):
            film = random.choice(film_ids)
            user = str(uuid.uuid4())
            t0 = time.perf_counter()
            _ = await mongo_toggle_and_query(mongo_col, film, user)
            latencies.append((time.perf_counter() - t0) * 1000.0)
        return latencies

    def worker_p() -> list[float]:
        latencies: list[float] = []
        iters = OPS // CONCURRENCY
        for _ in range(iters):
            film = random.choice(pg_films)
            user = str(uuid.uuid4())
            t0 = time.perf_counter()
            _ = pg_toggle_and_query(pg_cur, film, user)
            latencies.append((time.perf_counter() - t0) * 1000.0)
        return latencies

    # Mongo
    mongo_results = await asyncio.gather(
        *[worker_m() for _ in range(CONCURRENCY)],
    )
    mongo_lat = [ms for part in mongo_results for ms in part]
    mongo_lat.sort()
    m_p50 = mongo_lat[len(mongo_lat) // 2]
    m_p95 = mongo_lat[int(len(mongo_lat) * 0.95)]
    print(f"mongo  total p50={m_p50:5.2f} ms, p95={m_p95:5.2f} ms")

    # Postgres
    all_pg: list[float] = []
    for _ in range(CONCURRENCY):
        all_pg += worker_p()
    all_pg.sort()
    p_p50 = all_pg[len(all_pg) // 2]
    p_p95 = all_pg[int(len(all_pg) * 0.95)]
    print(f"pg     total p50={p_p50:5.2f} ms, p95={p_p95:5.2f} ms")


if __name__ == "__main__":
    asyncio.run(run())
