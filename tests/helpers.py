import uuid
from typing import Dict
from httpx import AsyncClient


def new_user() -> str:
    return str(uuid.uuid4())


def new_film() -> str:
    return str(uuid.uuid4())


def uid_header(user_id: str) -> Dict[str, str]:
    return {"X-User-Id": user_id}


async def read_stats(client: AsyncClient, film_id: str) -> dict:
    r = await client.get(f"/api/v1/film-stats/{film_id}")
    assert r.status_code == 200
    return r.json()
