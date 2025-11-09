from __future__ import annotations
from typing import Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


class ReviewVotesRepo:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.col = db["review_votes"]

    async def get_user_vote(
            self,
            review_id: str,
            user_id: str,
            session=None) -> Optional[str]:
        d = await self.col.find_one(
            {"review_id": ObjectId(review_id), "user_id": user_id},
            session=session,
        )
        return d["value"] if d else None

    async def upsert_vote(
            self,
            review_id: str,
            user_id: str,
            value: str, session=None) -> None:
        await self.col.update_one(
            {"review_id": ObjectId(review_id), "user_id": user_id},
            {"$set": {"value": value}},
            upsert=True,
            session=session,
        )

    async def delete_vote(
            self,
            review_id: str,
            user_id: str,
            session=None) -> bool:
        res = await self.col.delete_one(
            {"review_id": ObjectId(review_id), "user_id": user_id},
            session=session,
        )
        return res.deleted_count == 1

    async def delete_many_by_review(
            self,
            review_id: str,
            session=None) -> None:
        await self.col.delete_many(
            {"review_id": ObjectId(review_id)},
            session=session)
