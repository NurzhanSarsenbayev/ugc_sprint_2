"""Mongo repository for ratings collection."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional, Sequence, cast

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument


class RatingsRepo:
    """CRUD and aggregation helpers for ratings."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.col = db["ratings"]

    async def upsert(
        self,
        user_id: str,
        film_id: str,
        score: int,
    ) -> Dict[str, Any]:
        """Upsert rating for (user, film) and return updated document."""
        now = datetime.now(timezone.utc)
        doc = await self.col.find_one_and_update(
            {"user_id": user_id, "film_id": film_id},
            {
                "$set": {"score": score, "updated_at": now},
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        assert doc is not None
        return cast(dict[str, Any], doc)

    async def find_user_film(
        self,
        user_id: str,
        film_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Find rating for (user, film) pair (projection: score only)."""
        return await self.col.find_one(
            {"user_id": user_id, "film_id": film_id},
            {"_id": 0, "score": 1},
        )

    async def delete(self, user_id: str, film_id: str) -> bool:
        """Delete rating for (user, film)."""
        result = await self.col.delete_one(
            {"user_id": user_id, "film_id": film_id},
        )
        return result.deleted_count == 1

    async def list_by_user(
        self,
        user_id: str,
        limit: int,
        offset: int,
    ) -> List[Dict[str, Any]]:
        """List user ratings with pagination (newest first)."""
        cursor = (
            self.col.find({"user_id": user_id}, {"_id": 0})
            .sort("updated_at", -1)
            .skip(offset)
            .limit(limit)
        )
        return [doc async for doc in cursor]

    async def film_aggregate(self, film_id: str) -> Dict[str, Any]:
        """Aggregate film rating stats."""
        pipeline: list[dict[str, Any]] = [
            {"$match": {"film_id": film_id}},
            {
                "$group": {
                    "_id": "$film_id",
                    "ratings_count": {"$sum": 1},
                    "ratings_sum": {"$sum": "$score"},
                    "avg_rating": {"$avg": "$score"},
                }
            },
        ]

        docs = await self.col.aggregate(cast(Sequence[Mapping[str, Any]], pipeline)).to_list(
            length=1
        )
        if not docs:
            return {"ratings_count": 0, "ratings_sum": 0, "avg_rating": 0.0}

        group = cast(Dict[str, Any], docs[0])
        avg = group.get("avg_rating")
        return {
            "ratings_count": int(group.get("ratings_count", 0)),
            "ratings_sum": int(group.get("ratings_sum", 0)),
            "avg_rating": 0.0 if avg is None else round(float(avg), 2),
        }
