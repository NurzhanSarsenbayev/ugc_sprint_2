from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional, cast

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

DEFAULT_DOC: Dict[str, Any] = {
    "likes": 0,
    "dislikes": 0,
    "ratings_count": 0,
    "ratings_sum": 0,
    "avg_rating": 0.0,
    "reviews_count": 0,
    "votes_up": 0,
    "votes_down": 0,
    "updated_at": datetime.now(timezone.utc),
}


class FilmStatsRepo:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._col = db["film_stats"]

    async def get_by_film_id(self, film_id: str) -> Optional[Dict[str, Any]]:
        doc = await self._col.find_one({"film_id": film_id}, {"_id": 0})
        return cast(Optional[Dict[str, Any]], doc)

    async def ensure_doc(self, film_id: str) -> Dict[str, Any]:
        set_on_insert = {
            "film_id": film_id,
            "likes": 0,
            "dislikes": 0,
            "ratings_count": 0,
            "ratings_sum": 0,
            "avg_rating": 0.0,
            "reviews_count": 0,
            "votes_up": 0,
            "votes_down": 0,
            "created_at": datetime.now(timezone.utc),
            # IMPORTANT: do not set updated_at here
        }
        doc = await self._col.find_one_and_update(
            {"film_id": film_id},
            {"$setOnInsert": set_on_insert, "$currentDate": {"updated_at": True}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
            projection={"_id": 0},
        )
        assert doc is not None
        return cast(Dict[str, Any], doc)

    async def apply_inc_and_set(
        self,
        film_id: str,
        inc: Dict[str, Any] | None = None,
        set_: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """Merge $inc and $set safely. updated_at is always refreshed."""
        now = datetime.now(timezone.utc)
        update: Dict[str, Any] = {"$set": {"updated_at": now}}
        if inc:
            update["$inc"] = inc
        if set_:
            update["$set"].update(set_)

        doc = await self._col.find_one_and_update(
            {"film_id": film_id},
            update,
            upsert=True,
            return_document=ReturnDocument.AFTER,
            projection={"_id": 0},
        )
        assert doc is not None
        return cast(Dict[str, Any], doc)
