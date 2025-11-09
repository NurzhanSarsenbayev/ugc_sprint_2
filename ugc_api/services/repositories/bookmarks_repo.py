from __future__ import annotations
from datetime import datetime, timezone
from typing import List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase


class BookmarksRepo:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.col = db["bookmarks"]

    async def upsert(self, user_id: str, film_id: str) -> bool:
        """
        Возвращает created: True,
        если вставили новую запись (upserted_id != None).
        """
        now = datetime.now(timezone.utc)
        res = await self.col.update_one(
            {"user_id": user_id, "film_id": film_id},
            {"$setOnInsert": {"created_at": now}},
            upsert=True,
        )
        return res.upserted_id is not None

    async def delete(self, user_id: str, film_id: str) -> bool:
        res = await self.col.delete_one(
            {"user_id": user_id, "film_id": film_id})
        return res.deleted_count == 1

    async def list_by_user(
            self,
            user_id: str,
            limit: int,
            offset: int) -> List[Dict[str, Any]]:
        cur = (self.col.find({"user_id": user_id}, {"_id": 0, "film_id": 1})
               .sort("created_at", -1).skip(offset).limit(limit))
        return [d async for d in cur]

    async def count_by_user(self, user_id: str) -> int:
        return await self.col.count_documents({"user_id": user_id})
