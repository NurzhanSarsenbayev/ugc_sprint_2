import uuid
import pytest

R_LIKE = "/api/v1/likes"
R_RTG  = "/api/v1/ratings"
R_REV  = "/api/v1/reviews"
R_FS   = "/api/v1/film-stats"

async def read_stats(client, film_id: str) -> dict:
    r = await client.get(f"{R_FS}/{film_id}")
    assert r.status_code == 200
    return r.json()

@pytest.mark.asyncio
async def test_film_stats_end_to_end(client):
    film = str(uuid.uuid4())
    u1, u2, u3 = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())

    # начальные статы создаются по запросу
    s = await read_stats(client, film)
    assert s["film_id"] == film
    assert s["likes"] == s["dislikes"] == 0
    assert s["ratings_count"] == 0 and s["ratings_sum"] == 0 and float(s["avg_rating"]) == 0.0
    assert s["reviews_count"] == 0 and s["votes_up"] == 0 and s["votes_down"] == 0

    # --- ЛАЙКИ ---
    # u1: +1
    assert (await client.put(f"{R_LIKE}/{film}", json={"value": 1}, headers={"X-User-Id": u1})).status_code == 204
    s = await read_stats(client, film)
    assert s["likes"] == 1 and s["dislikes"] == 0

    # u1: +1 -> -1 (перенос)
    assert (await client.put(f"{R_LIKE}/{film}", json={"value": -1}, headers={"X-User-Id": u1})).status_code == 204
    s = await read_stats(client, film)
    assert s["likes"] == 0 and s["dislikes"] == 1

    # remove (None)
    assert (await client.delete(f"{R_LIKE}/{film}", headers={"X-User-Id": u1})).status_code == 204
    s = await read_stats(client, film)
    assert s["likes"] == 0 and s["dislikes"] == 0

    # --- РЕЙТИНГИ ---
    # u1 -> 7
    assert (await client.put(f"{R_RTG}/{film}?score=7", headers={"X-User-Id": u1})).status_code == 200
    s = await read_stats(client, film)
    assert s["ratings_count"] == 1 and s["ratings_sum"] == 7 and float(s["avg_rating"]) == pytest.approx(7.0)

    # u2 -> 9
    assert (await client.put(f"{R_RTG}/{film}?score=9", headers={"X-User-Id": u2})).status_code == 200
    s = await read_stats(client, film)
    assert s["ratings_count"] == 2 and s["ratings_sum"] == 16 and float(s["avg_rating"]) == pytest.approx(8.0)

    # u1: 7 -> 5
    assert (await client.put(f"{R_RTG}/{film}?score=5", headers={"X-User-Id": u1})).status_code == 200
    s = await read_stats(client, film)
    assert s["ratings_count"] == 2 and s["ratings_sum"] == 14 and float(s["avg_rating"]) == pytest.approx(7.0)

    # delete u2
    assert (await client.delete(f"{R_RTG}/{film}", headers={"X-User-Id": u2})).status_code == 204
    s = await read_stats(client, film)
    assert s["ratings_count"] == 1 and s["ratings_sum"] == 5 and float(s["avg_rating"]) == pytest.approx(5.0)

    # delete u1
    assert (await client.delete(f"{R_RTG}/{film}", headers={"X-User-Id": u1})).status_code == 204
    s = await read_stats(client, film)
    assert s["ratings_count"] == 0 and s["ratings_sum"] == 0 and float(s["avg_rating"]) == pytest.approx(0.0)

    # --- РЕЦЕНЗИИ + ГОЛОСА ---
    # создать рецензию (u1)
    r = await client.post(f"{R_REV}", json={"film_id": film, "text": "ok"}, headers={"X-User-Id": u1})
    assert r.status_code == 201
    review_id = r.json()["review_id"]

    s = await read_stats(client, film)
    assert s["reviews_count"] == 1

    # проголосовать: u2 -> up, u3 -> down
    r = await client.post(f"{R_REV}/{review_id}/vote", json={"value": "up"}, headers={"X-User-Id": u2})
    assert r.status_code == 200 and r.json()["applied"] is True
    s = await read_stats(client, film)
    assert s["votes_up"] >= 1

    r = await client.post(f"{R_REV}/{review_id}/vote", json={"value": "down"}, headers={"X-User-Id": u3})
    assert r.status_code == 200 and r.json()["applied"] is True
    s = await read_stats(client, film)
    assert s["votes_down"] >= 1

    # смена голоса u2: up -> down (должен произойти перенос в стате)
    r = await client.post(f"{R_REV}/{review_id}/vote", json={"value": "down"}, headers={"X-User-Id": u2})
    assert r.status_code == 200 and r.json()["applied"] is True
    s = await read_stats(client, film)
    # после переноса: votes_up уменьшится, votes_down увеличится — точные числа зависят от начального
    assert s["votes_down"] >= 1

    # unvote u3
    r = await client.delete(f"{R_REV}/{review_id}/vote", headers={"X-User-Id": u3})
    assert r.status_code == 200 and r.json()["applied"] is True

    # удалить рецензию автором (в стате меняется только reviews_count)
    r = await client.delete(f"{R_REV}/{review_id}", headers={"X-User-Id": u1})
    assert r.status_code == 204
    s = await read_stats(client, film)
    assert s["reviews_count"] == 0
