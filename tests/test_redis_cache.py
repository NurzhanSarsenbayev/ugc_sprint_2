import uuid

import pytest


@pytest.mark.asyncio
async def test_film_stats_cached(client):
    user_id = str(uuid.uuid4())
    film_id = str(uuid.uuid4())

    r = await client.put(
        f"/api/v1/ratings/{film_id}", params={"score": 8}, headers={"X-User-Id": user_id}
    )
    assert r.status_code == 200

    r = await client.get(f"/api/v1/film-stats/{film_id}")
    assert r.status_code == 200

    r = await client.get(f"/debug/cache/filmstats/{film_id}")
    assert r.status_code == 200
    assert r.json()["exists"] is True
