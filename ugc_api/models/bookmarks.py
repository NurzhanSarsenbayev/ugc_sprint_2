from pydantic import BaseModel
from typing import List


class BookmarkPutResponse(BaseModel):
    ok: bool
    created: bool


class BookmarkDeleteResponse(BaseModel):
    ok: bool
    deleted: bool


class BookmarkItem(BaseModel):
    film_id: str


class BookmarkListResponse(BaseModel):
    items: List[BookmarkItem]
    total: int
