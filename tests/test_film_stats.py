import pytest
from tests.helpers import new_user, new_film, uid_header, read_stats


async def test_film_stats_initial_is_zeroed(client):
    s = await read_stats(client, new_film())
    assert s["likes"] == 0 and s["dislikes"] == 0 and s["reviews_count"] == 0


async def test_film_stats_change_after_like_and_rating(client):
    film, user = new_film(), new_user()
    await client.put(f"/api/v1/likes/{film}",
                     json={"value": 1},
                     headers=uid_header(user))
    await client.put(f"/api/v1/ratings/{film}?score=7",
                     headers=uid_header(user))
    s = await read_stats(client, film)
    assert (s["likes"] == 1
            and s["ratings_count"] == 1
            and float(s["avg_rating"]) == pytest.approx(7.0))
