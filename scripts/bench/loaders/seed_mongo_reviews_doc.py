"""Seed Mongo 'reviews_doc' collection for document-vs-rel benchmarks."""

from __future__ import annotations

import asyncio
import os
import random
import uuid
from datetime import datetime, timedelta, timezone

from motor.motor_asyncio import AsyncIOMotorClient


TOTAL = int(os.getenv("TOTAL", "500_000"))
FILMS = int(os.getenv("FILMS", "5_000"))  # ~100 reviews per film
MONGO_DSN = os.getenv(
    "MONGO_DSN",
    "mongodb://mongo:27017/engagement_bench?replicaSet=rs0",
)
K_LAST = int(os.getenv("K_LAST", "20"))  # reserved, last votes tail size


async def main() -> None:
    """Create indexes and seed synthetic reviews."""
    cli = AsyncIOMotorClient(MONGO_DSN)
    db = cli.get_default_database()
    col = db["reviews_doc"]

    # start fresh for deterministic benchmarks
    await col.drop()

    # indexes
    await col.create_index(
        [("film_id", 1), ("hot", -1), ("created_at", -1)],
    )
    await col.create_index([("attrs.badge", 1)])  # sparse-like field
    # TTL for demo purposes (not used by benchmarks directly)
    await col.create_index("expires_at", expireAfterSeconds=0)

    now = datetime.now(timezone.utc)

    docs: list[dict] = []
    step = TOTAL // FILMS or 1
    last_film_id = str(uuid.uuid4())

    for i in range(TOTAL):
        if i % step == 0:
            last_film_id = str(uuid.uuid4())

        film_id = last_film_id
        attrs: dict[str, str] = {}
        if random.random() < 0.3:
            attrs["badge"] = random.choice(["critic", "verified"])

        doc = {
            "film_id": film_id,
            "user_id": str(uuid.uuid4()),
            "text": "lorem",
            "created_at": now - timedelta(
                seconds=random.randint(0, 3600 * 24 * 7),
            ),
            "hot": random.randint(0, 1000),
            "counters": {"up": 0, "down": 0},
            # last K votes tail (kept empty on seed, filled during runs)
            "last_votes": [],
            "attrs": attrs,
            "expires_at": now + timedelta(days=365),
        }
        docs.append(doc)

        if len(docs) == 10_000:
            await col.insert_many(docs)
            docs.clear()

    if docs:
        await col.insert_many(docs)

    print("mongo_reviews_doc seeded")


if __name__ == "__main__":
    asyncio.run(main())
