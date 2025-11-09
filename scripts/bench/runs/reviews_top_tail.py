"""Benchmark: top-20 reviews + last-5 votes (Mongo vs Postgres)."""

from __future__ import annotations

import asyncio
import os
import time
import uuid
from typing import List

from motor.motor_asyncio import AsyncIOMotorClient

MONGO_DSN = os.getenv(
    "MONGO_DSN",
    "mongodb://mongo:27017/engagement_bench?replicaSet=rs0",
)
PG_DSN = os.getenv("PG_DSN", "postgresql://bench:bench@postgres:5432/bench")
FILM_ID = os.getenv("FILM_ID", None) or str(uuid.uuid4())
OPS = int(os.getenv("OPS", "1000"))
CONC = int(os.getenv("CONCURRENCY", "10"))


def pct(values: List[float], p: float) -> float:
    """Percentile helper (linear interpolation)."""
    if not values:
        return 0.0
    k = (len(values) - 1) * p / 100.0
    flo = int(k)
    cei = min(flo + 1, len(values) - 1)
    if flo == cei:
        return values[flo]
    return values[flo] * (cei - k) + values[cei] * (k - flo)


# ---------- Mongo query ----------


async def mongo_query_once(client: AsyncIOMotorClient) -> float:
    """Run single Mongo query and return latency in ms."""
    db = client.get_default_database()
    col = db["bench_reviews"]

    t0 = time.perf_counter()
    cursor = (
        col.find(
            {"film_id": FILM_ID},
            projection={
                "votes": {"$slice": -5},
                "text": 1,
                "created_at": 1,
                "votes_counters": 1,
            },
        )
        .sort([("votes_counters.up", -1), ("created_at", -1)])
        .limit(20)
    )
    res = [doc async for doc in cursor]
    # sanity: max 20 documents
    assert len(res) <= 20
    return (time.perf_counter() - t0) * 1000.0


# ---------- PG query ----------


PG_SQL = """
SELECT r.id, r.text, r.created_at, r.up_cnt, r.down_cnt,
       lv.user_id, lv.value, lv.ts
FROM bench_reviews r
LEFT JOIN LATERAL (
  SELECT user_id, value, ts
  FROM bench_review_votes v
  WHERE v.review_id = r.id
  ORDER BY ts DESC
  LIMIT 5
) lv ON TRUE
WHERE r.film_id = %s
ORDER BY r.up_cnt DESC, r.created_at DESC
LIMIT 20;
"""


def pg_query_once_conn(conn) -> float:
    """Run single Postgres query on an existing connection; return ms."""
    t0 = time.perf_counter()
    with conn.cursor() as cur:
        cur.execute(PG_SQL, (FILM_ID,))
        _ = cur.fetchall()
    return (time.perf_counter() - t0) * 1000.0


async def run_mongo() -> dict:
    """Execute Mongo queries concurrently; return percentiles."""
    client = AsyncIOMotorClient(MONGO_DSN)
    latencies: List[float] = []
    sem = asyncio.Semaphore(CONC)

    async def worker() -> None:
        async with sem:
            latencies.append(await mongo_query_once(client))

    tasks = [asyncio.create_task(worker()) for _ in range(OPS)]
    await asyncio.gather(*tasks)
    client.close()

    latencies.sort()
    return {
        "p50": pct(latencies, 50),
        "p95": pct(latencies, 95),
        "n": len(latencies)}


def run_pg() -> dict:
    """Execute Postgres queries with a connection pool; return percentiles."""
    latencies: List[float] = []

    # pool sized to concurrency
    from psycopg_pool import ConnectionPool  # local import to avoid CI deps

    with (ConnectionPool(PG_DSN, min_size=1, max_size=CONC) as pool):
        # warm-up
        with pool.connection() as warm_conn:
            pg_query_once_conn(warm_conn)

        import concurrent.futures

        def worker() -> float:
            with pool.connection() as conn:
                return pg_query_once_conn(conn)

        with concurrent.futures.ThreadPoolExecutor(max_workers=CONC
                                                   ) as executor:
            for ms in executor.map(lambda _: worker(), range(OPS)):
                latencies.append(ms)

    latencies.sort()
    return {
        "p50": pct(latencies, 50),
        "p95": pct(latencies, 95),
        "n": len(latencies)}


async def main() -> None:
    """Run both benches and print summary."""
    print(f"OPS={OPS}, CONCURRENCY={CONC}")
    print("== Reviews: top-20 + last-5 votes (one shot) ==")

    print("== Mongo ==")
    m = await run_mongo()
    print(
        "mongo  query p50={:.2f} ms, p95={:.2f} ms, n={}".format(
            m["p50"],
            m["p95"],
            m["n"],
        ),
    )

    print("== Postgres ==")
    p = run_pg()
    print(
        "pg     query p50={:.2f} ms, p95={:.2f} ms, n={}".format(
            p["p50"],
            p["p95"],
            p["n"],
        ),
    )


if __name__ == "__main__":
    asyncio.run(main())
