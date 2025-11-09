"""Benchmark: ratings upsert + get + film aggregate (Mongo vs Postgres)."""

from __future__ import annotations

import asyncio
import os
import random
import time
import uuid
from typing import List

from motor.motor_asyncio import AsyncIOMotorClient
import psycopg


# --------- parameters ----------

OPS = int(os.getenv("OPS", "20000"))
CONCURRENCY = int(os.getenv("CONCURRENCY", "20"))

MONGO_DSN = os.getenv(
    "MONGO_DSN",
    "mongodb://localhost:27017/engagement_bench?replicaSet=rs0",
)
PG_DSN = os.getenv("PG_DSN", "postgresql://bench:bench@localhost:5432/bench")


# --------- helpers ----------


def pct(values: List[float], p: float) -> float:
    """Return percentile (nearest-rank over sorted values)."""
    if not values:
        return 0.0
    values_sorted = sorted(values)
    idx = int(round((p / 100.0) * (len(values_sorted) - 1)))
    return values_sorted[idx]


# --------- Mongo scenario ----------


async def bench_mongo():
    """Run Mongo scenario: upsert -> get -> aggregate."""
    client = AsyncIOMotorClient(MONGO_DSN)
    db_name = MONGO_DSN.split("/")[-1].split("?")[0]
    db = client[db_name]
    col = db["ratings_bench"]

    async def op():
        # scenario: upsert, then get user rating, then film aggregate
        film_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())

        t0 = time.perf_counter()
        await col.update_one(
            {"film_id": film_id, "user_id": user_id},
            {"$set": {"score": random.randint(1, 10)}},
            upsert=True,
        )
        t1 = time.perf_counter()

        _ = await col.find_one(
            {"film_id": film_id, "user_id": user_id},
            {"score": 1},
        )
        t2 = time.perf_counter()

        pipeline = [
            {"$match": {"film_id": film_id}},
            {
                "$group": {
                    "_id": "$film_id",
                    "count": {"$sum": 1},
                    "sum": {"$sum": "$score"},
                },
            },
        ]
        _ = [a async for a in col.aggregate(pipeline)]
        t3 = time.perf_counter()

        return (t1 - t0, t2 - t1, t3 - t2)

    lat_up: List[float] = []
    lat_get: List[float] = []
    lat_agg: List[float] = []

    sem = asyncio.Semaphore(CONCURRENCY)

    async def worker():
        async with sem:
            up, get, agg = await op()
        lat_up.append(up)
        lat_get.append(get)
        lat_agg.append(agg)

    await asyncio.gather(*[worker() for _ in range(OPS)])
    client.close()
    return lat_up, lat_get, lat_agg


# --------- Postgres scenario ----------


def bench_pg():
    """Run Postgres scenario: upsert -> get -> aggregate."""
    lat_up: List[float] = []
    lat_get: List[float] = []
    lat_agg: List[float] = []

    with psycopg.connect(PG_DSN, autocommit=True) as conn:
        with conn.cursor() as cur:
            for _ in range(OPS):
                film_id = str(uuid.uuid4())
                user_id = str(uuid.uuid4())
                score = random.randint(1, 10)

                t0 = time.perf_counter()
                cur.execute(
                    """
                    INSERT INTO ratings (film_id, user_id, score)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (film_id, user_id)
                    DO UPDATE SET score = EXCLUDED.score
                    """,
                    (film_id, user_id, score),
                )
                t1 = time.perf_counter()

                cur.execute(
                    """
                    SELECT score
                    FROM ratings
                    WHERE film_id = %s AND user_id = %s
                    """,
                    (film_id, user_id),
                )
                _ = cur.fetchone()
                t2 = time.perf_counter()

                cur.execute(
                    """
                    SELECT COUNT(*), AVG(score)
                    FROM ratings
                    WHERE film_id = %s
                    """,
                    (film_id,),
                )
                _ = cur.fetchone()
                t3 = time.perf_counter()

                lat_up.append(t1 - t0)
                lat_get.append(t2 - t1)
                lat_agg.append(t3 - t2)

    return lat_up, lat_get, lat_agg


def show(
        name: str,
        up: List[float],
        get: List[float],
        agg: List[float]) -> None:
    """Print p50/p95 for each phase and total."""
    def line(label: str, values: List[float]) -> None:
        print(
            f"{name:<6} {label:<6} "
            f"p50={pct(values, 50) * 1000:6.2f} ms, "
            f"p95={pct(values, 95) * 1000:6.2f} ms, "
            f"n={len(values)}",
        )

    line("upsert", up)
    line("get", get)
    line("agg", agg)

    total = [u + g + a for u, g, a in zip(up, get, agg)]
    print(
        f"{name:<6} total  "
        f"p50={pct(total, 50) * 1000:6.2f} ms, "
        f"p95={pct(total, 95) * 1000:6.2f} ms",
    )


async def main() -> None:
    """Run both benches and print the summary."""
    print(f"OPS={OPS}, CONCURRENCY={CONCURRENCY}")

    print("== Mongo ==")
    mu, mg, ma = await bench_mongo()
    show("mongo", mu, mg, ma)

    print("== Postgres ==")
    pu, pg, pa = bench_pg()
    show("pg", pu, pg, pa)


if __name__ == "__main__":
    asyncio.run(main())
