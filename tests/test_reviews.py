from bson import ObjectId
from tests.helpers import new_user, new_film, uid_header, read_stats

BASE = "/api/v1/reviews"


async def test_review_create_and_get_by_id(client):
    film, author = new_film(), new_user()
    r = await client.post(BASE, json={"film_id": film,
                                      "text": "hello"},
                          headers=uid_header(author))
    assert r.status_code == 201
    rid = r.json()["review_id"]
    r = await client.get(f"{BASE}/{rid}")
    assert r.status_code == 200 and r.json()["film_id"] == film


async def test_review_update_forbidden_for_stranger_returns_404(client):
    film, author, stranger = new_film(), new_user(), new_user()
    rid = (await client.post(BASE, json={"film_id": film,
                                         "text": "t"},
                             headers=uid_header(author))).json()["review_id"]
    r = await client.patch(f"{BASE}/{rid}",
                           json={"text": "x"},
                           headers=uid_header(stranger))
    assert r.status_code == 404  # «не найдено или не автор»


async def test_review_delete_by_author_then_get_returns_404(client):
    film, author = new_film(), new_user()
    rid = (await client.post(BASE, json={"film_id": film,
                                         "text": "t"},
                             headers=uid_header(author))).json()["review_id"]
    r = await client.delete(f"{BASE}/{rid}", headers=uid_header(author))
    assert r.status_code == 204
    r = await client.get(f"{BASE}/{rid}")
    assert r.status_code == 404


async def test_reviews_list_sorted_new_contains_recent_items(client):
    film, author = new_film(), new_user()
    r1 = await client.post(BASE, json={"film_id": film,
                                       "text": "a"},
                           headers=uid_header(author))
    r2 = await client.post(BASE, json={"film_id": film,
                                       "text": "b"},
                           headers=uid_header(author))
    r = await client.get(f"{BASE}/films/{film}?limit=10&offset=0&sort=new")
    got = [i["review_id"] for i in r.json()["items"]]
    assert {r1.json()["review_id"], r2.json()["review_id"]}.issubset(set(got))


async def test_reviews_list_sorted_top_orders_by_votes_up_then_created_desc(
        client):
    film, u1, u2 = new_film(), new_user(), new_user()
    r1 = await client.post(BASE, json={"film_id": film,
                                       "text": "a"},
                           headers=uid_header(u1))
    r2 = await client.post(BASE, json={"film_id": film,
                                       "text": "b"},
                           headers=uid_header(u1))
    rid1, rid2 = r1.json()["review_id"], r2.json()["review_id"]
    # прокачаем второй отзыв (votes.up = 1)
    await client.post(f"{BASE}/{rid2}/vote",
                      json={"value": "up"},
                      headers=uid_header(u2))

    r = await client.get(f"{BASE}/films/{film}?limit=10&offset=0&sort=top")
    items = r.json()["items"]
    ids = [i["review_id"] for i in items]
    # ожидаем, что rid2 (больше up) стоит раньше rid1
    assert ids.index(rid2) < ids.index(rid1)


async def test_review_votes_up_down_unvote_updates_stats(client):
    film, u = new_film(), new_user()
    rid = (await client.post(BASE, json={"film_id": film,
                                         "text": "ok"},
                             headers=uid_header(u))).json()["review_id"]

    await client.post(f"{BASE}/{rid}/vote",
                      json={"value": "up"},
                      headers=uid_header(u))
    s = await read_stats(client, film)
    assert s["votes_up"] == 1 and s["votes_down"] == 0

    await client.post(f"{BASE}/{rid}/vote",
                      json={"value": "down"},
                      headers=uid_header(u))
    s = await read_stats(client, film)
    assert s["votes_up"] == 0 and s["votes_down"] == 1

    await client.delete(f"{BASE}/{rid}/vote", headers=uid_header(u))
    s = await read_stats(client, film)
    assert s["votes_up"] == 0 and s["votes_down"] == 0


async def test_get_nonexistent_review_returns_404(client):
    # валидный, но несуществующий ObjectId
    rnd = str(ObjectId())
    r = await client.get(f"{BASE}/{rnd}")
    assert r.status_code == 404


async def test_delete_by_stranger_returns_404(client):
    film, author, stranger = new_film(), new_user(), new_user()
    rid = (await client.post(
        BASE, json={"film_id": film, "text": "t"}, headers=uid_header(author)
    )).json()["review_id"]

    r = await client.delete(f"{BASE}/{rid}", headers=uid_header(stranger))
    assert r.status_code == 404  # review_not_found_or_not_author
