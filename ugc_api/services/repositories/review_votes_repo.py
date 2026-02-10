from __future__ import annotations

from typing import Any, cast

from motor.motor_asyncio import AsyncIOMotorDatabase


class ReviewVotesRepo:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.col = db["review_votes"]

    async def get_user_vote(
        self,
        review_id: str,
        user_id: str,
        session: Any | None = None,
    ) -> str | None:
        doc = await self.col.find_one({"review_id": review_id, "user_id": user_id}, session=session)
        if not doc:
            return None
        return cast(str, doc.get("value"))

    async def upsert_vote(
        self,
        review_id: str,
        user_id: str,
        value: str,
        session: Any | None = None,
    ) -> None:
        await self.col.update_one(
            {"review_id": review_id, "user_id": user_id},
            {"$set": {"value": value}},
            upsert=True,
            session=session,
        )

    async def delete_vote(
        self,
        review_id: str,
        user_id: str,
        session: Any | None = None,
    ) -> bool:
        res = await self.col.delete_one(
            {"review_id": review_id, "user_id": user_id}, session=session
        )
        return bool(res.deleted_count == 1)

    async def delete_many_by_review(
        self,
        review_id: str,
        session: Any | None = None,
    ) -> int:
        res = await self.col.delete_many({"review_id": review_id}, session=session)
        return int(res.deleted_count)
