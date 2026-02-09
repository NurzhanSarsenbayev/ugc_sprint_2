import os
import asyncio
import random
import time
import sys
import statistics as st
import psycopg
from motor.motor_asyncio import AsyncIOMotorClient

OPS = int(os.getenv("OPS", "200"))
K = int(os.getenv("K", "100"))  # number of films per query
TOPN = int(os.getenv("TOPN", "3"))

MONGO_DSN = os.getenv("MONGO_DSN")
PG_DSN = os.getenv("PG_DSN")

# Force line-buffered stdout (useful in Docker/CI logs)
try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass


async def pick_film_ids_mongo():
    """Fast path: distinct film_ids (avoid heavy aggregation)."""
    cli = AsyncIOMotorClient(MONGO_DSN)
    col = cli.get_default_database()["bench_reviews"]
    ids = await col.distinct("film_id")
    ids = [d for d in ids if d]
    random.shuffle(ids)
    return ids[:K]


async def query_mongo(film_ids):
    """Aggregation: top-N reviews per film."""
    cli = AsyncIOMotorClient(MONGO_DSN)
    col = cli.get_default_database()["bench_reviews"]
    pipeline = [
        {"$match": {"film_id": {"$in": film_ids}}},
        {"$sort": {"votes_counters.up": -1, "created_at": -1}},
        {"$group": {
            "_id": "$film_id",
            "top": {"$topN": {
                "n": TOPN,
                "sortBy": {"votes_counters.up": -1, "created_at": -1},
                "output": {
                    "_id": "$_id", "user_id": "$user_id", "text": "$text",
                    "up": "$votes_counters.up", "created_at": "$created_at"
                }
            }}
        }},
        {"$project": {"_id": 0, "film_id": "$_id", "top": 1}}
    ]
    t0 = time.perf_counter()
    # maxTimeMS prevents hanging; allowDiskUse is a safety net
    cursor = col.aggregate(pipeline, allowDiskUse=True, maxTimeMS=15000)
    _ = [d async for d in cursor]
    return (time.perf_counter() - t0) * 1000.0


def query_pg(conn, film_ids):
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
        cur.execute(sql, (film_ids, TOPN))
        _ = cur.fetchall()
    return (time.perf_counter() - t0) * 1000.0


async def main():
    film_ids = await pick_film_ids_mongo()
    if not film_ids:
        print("No film_ids in Mongo;"
              " nothing to query. (seed more or lower K/TOPN)")
        return
    else:
        print(f"Using {len(film_ids)} film_ids from Mongo")

    # Warm-up
    _ = await query_mongo(film_ids)
    with psycopg.connect(PG_DSN) as conn:
        _ = query_pg(conn, film_ids)

        mongo_ms = []
        pg_ms = []
        for _ in range(OPS):
            mongo_ms.append(await query_mongo(film_ids))
            pg_ms.append(query_pg(conn, film_ids))

    def pr(name, arr):
        # p95 via quantiles
        print(f"{name:6s} p50={st.median(arr):6.2f} ms,"
              f" p95={st.quantiles(arr, n=100)[94]:6.2f} ms, n={len(arr)}")

    print("== TopN per many films ==")
    pr("mongo", mongo_ms)
    pr("pg", pg_ms)


if __name__ == "__main__":
    asyncio.run(main())
