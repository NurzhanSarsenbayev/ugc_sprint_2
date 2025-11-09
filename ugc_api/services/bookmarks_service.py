"""Service layer for managing user bookmarks."""

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import PyMongoError

from ugc_api.models.bookmarks import (
    BookmarkDeleteResponse,
    BookmarkItem,
    BookmarkListResponse,
    BookmarkPutResponse,
)
from .repositories.bookmarks_repo import BookmarksRepo


class BookmarksService:
    """CRUD operations for user bookmarks."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        """Initialize repository."""
        self.repo = BookmarksRepo(db)

    async def add_bookmark(
        self,
        user_id: str,
        film_id: str,
    ) -> BookmarkPutResponse:
        """Create or update a bookmark for the given film."""
        try:
            created = await self.repo.upsert(
                user_id=user_id,
                film_id=film_id,
            )
            return BookmarkPutResponse(ok=True, created=created)
        except PyMongoError as error:
            raise RuntimeError(f'mongo_bookmark_add_error: {error}') from error

    async def remove_bookmark(
        self,
        user_id: str,
        film_id: str,
    ) -> BookmarkDeleteResponse:
        """Delete a bookmark for the given film."""
        try:
            deleted = await self.repo.delete(
                user_id=user_id,
                film_id=film_id,
            )
            return BookmarkDeleteResponse(ok=True, deleted=deleted)
        except PyMongoError as error:
            raise RuntimeError(
                f'mongo_bookmark_remove_error: {error}') from error

    async def list_bookmarks(
        self,
        user_id: str,
        limit: int,
        offset: int,
    ) -> BookmarkListResponse:
        """List all user bookmarks with pagination."""
        try:
            docs = await self.repo.list_by_user(
                user_id=user_id,
                limit=limit,
                offset=offset,
            )
            total = await self.repo.count_by_user(user_id=user_id)
            items = [BookmarkItem(film_id=doc['film_id']) for doc in docs]
            return BookmarkListResponse(items=items, total=total)
        except PyMongoError as error:
            raise RuntimeError(
                f'mongo_bookmark_list_error: {error}') from error
