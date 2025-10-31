from typing import Any
from pymongo import MongoClient
from ugc_api.core.config import settings

_client: MongoClient | None = None

def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(settings.mongo_dsn)
    return _client

def get_db():
    return get_client()[settings.mongo_db]

def col(name: str):
    return get_db()[name]

_client = MongoClient(settings.mongo_dsn)
db = _client[settings.mongo_db]
ratings = db["ratings"]  # {user_id, film_id, value:int, updated_at}
bookmarks = db["bookmarks"]  # {user_id, film_id, created_at}
reviews = db["reviews"]  # {review_id, user_id, film_id, text, created_at, votes: {up:int, down:int}}
