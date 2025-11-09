from pydantic import BaseModel, Field
from enum import Enum
from typing import List
from datetime import datetime


class ReviewCreateRequest(BaseModel):
    film_id: str
    text: str


class ReviewCreateResponse(BaseModel):
    review_id: str


class ReviewItem(BaseModel):
    review_id: str
    film_id: str
    user_id: str
    text: str
    up: int
    down: int
    created_at: datetime


class ReviewListResponse(BaseModel):
    items: List[ReviewItem]
    total: int


class ReviewUpdateRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10_000)


class ReviewUpdateResponse(BaseModel):
    ok: bool


class VoteValue(str, Enum):
    up = "up"
    down = "down"


class ReviewVoteRequest(BaseModel):
    value: VoteValue


class ReviewVoteResponse(BaseModel):
    ok: bool
    applied: bool
