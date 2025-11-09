"""Tests for ratings API flows and RatingsService fallbacks."""

from __future__ import annotations

import pytest

from tests.helpers import new_film, new_user, read_stats, uid_header
from ugc_api.dependencies import get_db
from ugc_api.services.ratings_service import RatingsService


# ---------------------------------------------------------------------------


async def test_rating_put_returns_payload_and_updates_stats(client):
    film, user = new_film(), new_user()

    r = await client.put(
        f"/api/v1/ratings/{film}?score=7",
        headers=uid_header(user),
    )
    assert r.status_code == 200
    assert r.json() == {"film_id": film, "score": 7}

    s = await read_stats(client, film)
    assert s["ratings_count"] == 1
    assert s["ratings_sum"] == 7


async def test_rating_put_then_update_changes_avg(client):
    film, u1, u2 = new_film(), new_user(), new_user()

    await client.put(
        f"/api/v1/ratings/{film}?score=7",
        headers=uid_header(u1),
    )
    # update same user score
    await client.put(
        f"/api/v1/ratings/{film}?score=9",
        headers=uid_header(u1),
    )
    await client.put(
        f"/api/v1/ratings/{film}?score=5",
        headers=uid_header(u2),
    )

    s = await read_stats(client, film)
    assert s["ratings_count"] == 2
    assert s["ratings_sum"] == 14
    assert float(s["avg_rating"]) == pytest.approx(7.0)


async def test_rating_same_score_twice_does_not_change_sum(client):
    film, u1 = new_film(), new_user()

    await client.put(
        f"/api/v1/ratings/{film}?score=7",
        headers=uid_header(u1),
    )
    s1 = await read_stats(client, film)

    # same score should not change sum
    await client.put(
        f"/api/v1/ratings/{film}?score=7",
        headers=uid_header(u1),
    )
    s2 = await read_stats(client, film)

    assert s1["ratings_sum"] == 7
    assert s2["ratings_sum"] == 7
    assert s2["ratings_count"] == 1


async def test_rating_delete_recomputes_stats(client):
    film, u1, u2 = new_film(), new_user(), new_user()

    await client.put(
        f"/api/v1/ratings/{film}?score=5",
        headers=uid_header(u1),
    )
    await client.put(
        f"/api/v1/ratings/{film}?score=9",
        headers=uid_header(u2),
    )

    r = await client.delete(
        f"/api/v1/ratings/{film}",
        headers=uid_header(u2),
    )
    assert r.status_code == 204

    s = await read_stats(client, film)
    assert s["ratings_count"] == 1
    assert s["ratings_sum"] == 5
    assert float(s["avg_rating"]) == 5.0


@pytest.mark.parametrize("score", [0, 11, -1, 100])
async def test_rating_put_out_of_range_returns_422(client, score):
    film, user = new_film(), new_user()

    r = await client.put(
        f"/api/v1/ratings/{film}?score={score}",
        headers=uid_header(user),
    )
    assert r.status_code == 422


async def test_rating_put_non_int_returns_422(client):
    film, user = new_film(), new_user()

    r = await client.put(
        f"/api/v1/ratings/{film}?score=nan",
        headers=uid_header(user),
    )
    assert r.status_code == 422


async def test_get_user_rating_initial_none_and_after_put(client):
    film, user = new_film(), new_user()

    # initially none
    r = await client.get(
        f"/api/v1/ratings/{film}",
        headers=uid_header(user),
    )
    assert r.status_code == 200
    assert r.json() == {
        "film_id": film,
        "user_id": user,
        "score": None,
    }

    # set value
    r = await client.put(
        f"/api/v1/ratings/{film}?score=8",
        headers=uid_header(user),
    )
    assert r.status_code == 200
    assert r.json() == {"film_id": film, "score": 8}

    # now GET returns 8
    r = await client.get(
        f"/api/v1/ratings/{film}",
        headers=uid_header(user),
    )
    assert r.status_code == 200
    assert r.json() == {
        "film_id": film,
        "user_id": user,
        "score": 8,
    }


async def test_ratings_service_fallback_stats_without_filmstats(client):
    film, u1, u2 = new_film(), new_user(), new_user()

    # populate via API
    await client.put(
        f"/api/v1/ratings/{film}?score=7",
        headers=uid_header(u1),
    )
    # update same user
    await client.put(
        f"/api/v1/ratings/{film}?score=9",
        headers=uid_header(u1),
    )
    await client.put(
        f"/api/v1/ratings/{film}?score=5",
        headers=uid_header(u2),
    )

    # use real DB with RatingsService but without FilmStatsService
    db = await get_db()
    svc = RatingsService(db, stats=None)

    # fallback branch should aggregate without FilmStatsService
    resp = await svc.film_stats(film_id=film)

    # FilmStatsResponse: film_id, avg_rating(Optional[float]),
    # likes:int, dislikes:int, count:int
    assert resp.film_id == film
    assert resp.count == 2
    assert pytest.approx(resp.avg_rating) == 7.0

    # likes/dislikes come from fallback aggregation (likely 0/0 here)
    assert isinstance(resp.likes, int)
    assert isinstance(resp.dislikes, int)


async def test_ratings_service_fallback_stats_for_empty_film():
    film = new_film()
    db = await get_db()
    svc = RatingsService(db, stats=None)

    resp = await svc.film_stats(film_id=film)

    # count=0, avg_rating=None for empty film; likes/dislikes are ints
    assert resp.film_id == film
    assert resp.count == 0
    assert resp.avg_rating is None
    assert isinstance(resp.likes, int)
    assert isinstance(resp.dislikes, int)
