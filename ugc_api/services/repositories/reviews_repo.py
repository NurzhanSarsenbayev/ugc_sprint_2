"""Mongo repository for reviews collection."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


class ReviewsRepo:
    """CRUD and voting helpers for reviews."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.col = db['reviews']

    @property
    def client(self):
        """Expose motor client to open transactions in services."""
        return self.col.database.client

    async def insert(
        self,
        film_id: str,
        user_id: str,
        text: str,
    ) -> str:
        """Insert a new review and return its id as string."""
        doc = {
            'film_id': film_id,
            'user_id': user_id,
            'text': text,
            'created_at': datetime.now(timezone.utc),
            'votes': {'up': 0, 'down': 0},
        }
        result = await self.col.insert_one(doc)
        return str(result.inserted_id)

    async def get_by_id(self, review_id: str) -> Optional[Dict[str, Any]]:
        """Get single review by its id."""
        return await self.col.find_one({'_id': ObjectId(review_id)})

    async def list_by_film(
        self,
        film_id: str,
        limit: int,
        offset: int,
        sort: str = 'new',
    ) -> List[Dict[str, Any]]:
        """List film reviews with sorting and pagination."""
        query = {'film_id': film_id}

        if sort == 'top':
            cursor = (
                self.col.find(query)
                .sort([('votes.up', -1), ('created_at', -1)])
                .skip(offset)
                .limit(limit)
            )
        else:
            cursor = (
                self.col.find(query)
                .sort('created_at', -1)
                .skip(offset)
                .limit(limit)
            )

        return [doc async for doc in cursor]

    async def count_by_film(self, film_id: str) -> int:
        """Count reviews by film id."""
        return await self.col.count_documents({'film_id': film_id})

    async def update_text(
        self,
        user_id: str,
        review_id: str,
        text: str,
    ) -> bool:
        """Update review text if user is the author."""
        result = await self.col.update_one(
            {'_id': ObjectId(review_id), 'user_id': user_id},
            {'$set': {'text': text}},
        )
        return result.modified_count == 1

    async def inc_votes(
        self,
        review_id: str,
        inc: Dict[str, int],
        session=None,
    ) -> bool:
        """Increment vote counters with $inc."""
        result = await self.col.update_one(
            {'_id': ObjectId(review_id)},
            {'$inc': inc},
            session=session,
        )
        return result.matched_count == 1

    async def delete(
        self,
        user_id: str,
        review_id: str,
        session=None,
    ) -> bool:
        """Delete review by id if user is the author."""
        result = await self.col.delete_one(
            {'_id': ObjectId(review_id), 'user_id': user_id},
            session=session,
        )
        return result.deleted_count == 1

    async def apply_vote_delta(
        self,
        review_id: str,
        old_vote: Optional[str],
        new_vote: Optional[str],
        *,
        session=None,
    ) -> bool:
        """Apply delta to votes.up/down according to old/new values."""
        inc: Dict[str, int] = {}

        if old_vote == 'up':
            inc['votes.up'] = inc.get('votes.up', 0) - 1
        if old_vote == 'down':
            inc['votes.down'] = inc.get('votes.down', 0) - 1

        if new_vote == 'up':
            inc['votes.up'] = inc.get('votes.up', 0) + 1
        if new_vote == 'down':
            inc['votes.down'] = inc.get('votes.down', 0) + 1

        if not inc:
            return True

        return await self.inc_votes(review_id, inc, session=session)

    async def get_film_id(
        self,
        review_id: str,
        *,
        session=None,
    ) -> Optional[str]:
        """Get film_id by review id (projection only)."""
        doc = await self.col.find_one(
            {'_id': ObjectId(review_id)},
            {'film_id': 1, '_id': 0},
            session=session,
        )
        return doc['film_id'] if doc else None

    async def delete_and_return(
        self,
        user_id: str,
        review_id: str,
        *,
        session=None,
    ) -> Optional[Dict[str, Any]]:
        """Delete review and return projection with film_id (for stats)."""
        doc = await self.col.find_one_and_delete(
            {'_id': ObjectId(review_id), 'user_id': user_id},
            session=session,
            projection={'film_id': 1, '_id': 1},
        )
        return doc
