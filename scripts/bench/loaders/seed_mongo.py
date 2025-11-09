"""Seed Mongo 'ratings_bench' collection with random ratings."""

from __future__ import annotations

import asyncio
import os
import random
import time
import uuid

from motor.motor_asyncio import AsyncIOMotorClient


MONGO_DSN = os.getenv(
    "MONGO_DSN",
    "mongodb://localhost:27017/engagement_bench?replicaSet=rs0",
)
DBNAME = MONGO_DSN.split("/")[-1].split("?")[0]
TOTAL = int(os.getenv("TOTAL", "1000000"))
BATCH = int(os.getenv("BATCH", "10000"))


async def main() -> None:
    """Create indexes and insert random rating documents in batches."""
    client = AsyncIOMotorClient(MONGO_DSN)
    db = client[DBNAME]
    col = db["ratings_bench"]

    # Indexes
    await col.create_index([("film_id", 1), ("user_id", 1)], unique=True)
    await col.create_index([("user_id", 1)])
    await col.create_index([("film_id", 1)])

    left = TOTAL
    t0 = time.time()

    while left > 0:
        n = min(BATCH, left)
        docs = [
            {
                "film_id": str(uuid.uuid4()),
                "user_id": str(uuid.uuid4()),
                "score": random.randint(1, 10),
            }
            for _ in range(n)
        ]
        await col.insert_many(docs, ordered=False)
        left -= n

    dt = time.time() - t0
    rate = int(TOTAL / dt) if dt > 0 else 0
    print(f"[mongo] inserted={TOTAL} in {dt:.1f}s ({rate} docs/s)")

    client.close()


if __name__ == "__main__":
    asyncio.run(main())
