"""Mongo repository for likes collection."""

from __future__ import annotations

from typing import Optional

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument
from pymongo.errors import PyMongoError


class LikesRepo:
    """CRUD helpers for like/dislike state."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._col = db['likes']

    async def ensure_indexes(self) -> None:
        """Create indexes: unique (film_id, user_id) and film_id filter."""
        await self._col.create_index(
            [('film_id', 1), ('user_id', 1)],
            unique=True,
        )
        await self._col.create_index([('film_id', 1)])

    async def get(self, film_id: str, user_id: str) -> Optional[int]:
        """Get current reaction value for (film, user)."""
        doc = await self._col.find_one(
            {'film_id': film_id, 'user_id': user_id},
            {'_id': 0, 'value': 1},
        )
        return None if doc is None else int(doc['value'])

    async def set(
        self,
        film_id: str,
        user_id: str,
        value: int,
    ) -> Optional[int]:
        """Idempotently set reaction; return previous value (or None)."""
        try:
            prev = await self._col.find_one_and_update(
                {'film_id': film_id, 'user_id': user_id},
                {'$set': {'value': value}},
                upsert=True,
                return_document=ReturnDocument.BEFORE,
                projection={'_id': 0, 'value': 1},
            )
            return None if prev is None else int(prev['value'])
        except PyMongoError:
            # Let service layer decide how to handle DB errors.
            raise

    async def delete(self, film_id: str, user_id: str) -> Optional[int]:
        """Delete reaction; return previous value (or None)."""
        try:
            prev = await self._col.find_one_and_delete(
                {'film_id': film_id, 'user_id': user_id},
                projection={'_id': 0, 'value': 1},
            )
            return None if prev is None else int(prev['value'])
        except PyMongoError:
            raise
