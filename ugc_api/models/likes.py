from __future__ import annotations
from pydantic import BaseModel, Field


class LikeSetRequest(BaseModel):
    value: int = Field(..., description="+1 or -1", ge=-1, le=1)


class LikeStateResponse(BaseModel):
    film_id: str
    user_id: str
    value: int | None = None  # None = реакции нет
