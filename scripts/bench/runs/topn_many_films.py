from __future__ import annotations

import asyncio
import os
import random
import statistics as st
import sys
import time
from typing import Any, Sequence

import psycopg
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorClient

OPS = int(os.getenv("OPS", "200"))
K = int(os.getenv("K", "100"))  # number of films per query
TOPN = int(os.getenv("TOPN", "3"))

# Progress log every N iterations (helps avoid "it hangs" feeling)
PROGRESS_EVERY = int(os.getenv("PROGRESS_EVERY", "10"))

MONGO_DSN = os.getenv("MONGO_DSN")
PG_DSN = os.getenv("PG_DSN")

# Force line-buffered stdout (useful in Docker/CI logs)
try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass


async def pick_film_ids_mongo(col: AsyncIOMotorCollection, limit: int) -> list[str]:
    """Fast path: distinct film_ids (avoid heavy aggregation)."""
    ids = await col.distinct("film_id")
    ids = [d for d in ids if d]
    random.shuffle(ids)
    return ids[:limit]


async def query_mongo(col: AsyncIOMotorCollection, film_ids: Sequence[str]) -> float:
    """Aggregation: top-N reviews per film."""
    pipeline: list[dict[str, Any]] = [
        {"$match": {"film_id": {"$in": list(film_ids)}}},
        {"$sort": {"votes_counters.up": -1, "created_at": -1}},
        {
            "$group": {
                "_id": "$film_id",
                "top": {
                    "$topN": {
                        "n": TOPN,
                        "sortBy": {"votes_counters.up": -1, "created_at": -1},
                        "output": {
                            "_id": "$_id",
                            "user_id": "$user_id",
                            "text": "$text",
                            "up": "$votes_counters.up",
                            "created_at": "$created_at",
                        },
                    }
                },
            }
        },
        {"$project": {"_id": 0, "film_id": "$_id", "top": 1}},
    ]

    t0 = time.perf_counter()
    cursor = col.aggregate(pipeline, allowDiskUse=True, maxTimeMS=15000)
    _ = [d async for d in cursor]
    return (time.perf_counter() - t0) * 1000.0


def query_pg(conn: psycopg.Connection, film_ids: Sequence[str]) -> float:
    """Postgres equivalent using normalized bench_reviews table."""
    if not film_ids:
        raise ValueError("film_ids is empty. Seed data or reduce K/TOPN.")

    sql = """
    WITH ranked AS (
        SELECT r.film_id, r.id, r.user_id, r.text, r.up_cnt, r.created_at,
               ROW_NUMBER() OVER (
                   PARTITION BY r.film_id
                   ORDER BY r.up_cnt DESC, r.created_at DESC
               ) AS rn
        FROM bench_reviews r
        WHERE r.film_id = ANY(%s::uuid[])
    )
    SELECT film_id, id, user_id, text, up_cnt, created_at
    FROM ranked
    WHERE rn <= %s;
    """

    t0 = time.perf_counter()
    with conn.cursor() as cur:
        cur.execute(sql, (list(film_ids), TOPN))
        _ = cur.fetchall()
    return (time.perf_counter() - t0) * 1000.0


def p95(arr: list[float]) -> float:
    # quantiles-based p95
    return st.quantiles(arr, n=100)[94]


def log_progress(i: int, total: int, last_mongo: float, last_pg: float) -> None:
    if PROGRESS_EVERY <= 0:
        return
    if (i + 1) % PROGRESS_EVERY == 0 or (i + 1) == total:
        print(
            f"progress {i + 1}/{total}: last mongo={last_mongo:6.2f} ms, last pg={last_pg:6.2f} ms"
        )


async def main() -> None:
    if not MONGO_DSN or not PG_DSN:
        raise RuntimeError("MONGO_DSN/PG_DSN must be set in environment.")

    mongo_cli = AsyncIOMotorClient(MONGO_DSN)
    try:
        col = mongo_cli.get_default_database()["bench_reviews"]

        film_ids = await pick_film_ids_mongo(col, K)
        if not film_ids:
            print("No film_ids in Mongo; nothing to query. (seed more or lower K/TOPN)")
            return

        print(f"Using {len(film_ids)} film_ids from Mongo")
        print(f"Params: OPS={OPS}, K={K}, TOPN={TOPN}, PROGRESS_EVERY={PROGRESS_EVERY}")

        # Warm-up (helps JIT-ish / caches, removes first-run penalties)
        _ = await query_mongo(col, film_ids)
        with psycopg.connect(PG_DSN) as conn:
            _ = query_pg(conn, film_ids)

            mongo_ms: list[float] = []
            pg_ms: list[float] = []

            for i in range(OPS):
                m = await query_mongo(col, film_ids)
                p = query_pg(conn, film_ids)
                mongo_ms.append(m)
                pg_ms.append(p)
                log_progress(i, OPS, m, p)

        print("== TopN per many films ==")
        print(
            f"mongo  p50={st.median(mongo_ms):6.2f} ms, p95={p95(mongo_ms):6.2f} ms, n={len(mongo_ms)}"
        )
        print(
            f"pg     p50={st.median(pg_ms):6.2f} ms, p95={p95(pg_ms):6.2f} ms, n={len(pg_ms)}"
        )

    finally:
        mongo_cli.close()


if __name__ == "__main__":
    asyncio.run(main())
