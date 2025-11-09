import uuid

async def test_ratings_stats(client):
    film = str(uuid.uuid4()); u1 = str(uuid.uuid4()); u2 = str(uuid.uuid4())

    # set 7, потом 9
    assert (await client.put(f"/api/v1/ratings/{film}?score=7", headers={"X-User-Id": u1})).status_code == 200
    assert (await client.put(f"/api/v1/ratings/{film}?score=9", headers={"X-User-Id": u1})).status_code == 200

    # второй ставит 5
    assert (await client.put(f"/api/v1/ratings/{film}?score=5", headers={"X-User-Id": u2})).status_code == 200

    # stats: count=2, sum=14, avg=7.0
    s = (await client.get(f"/api/v1/film-stats/{film}")).json()
    assert s["ratings_count"] == 2 and s["ratings_sum"] == 14 and s["avg_rating"] == 7.0

    # удаляем рейтинг u1 → count=1, sum=5, avg=5.0
    assert (await client.delete(f"/api/v1/ratings/{film}", headers={"X-User-Id": u1})).status_code == 204
    s = (await client.get(f"/api/v1/film-stats/{film}")).json()
    assert s["ratings_count"] == 1 and s["ratings_sum"] == 5 and s["avg_rating"] == 5.0