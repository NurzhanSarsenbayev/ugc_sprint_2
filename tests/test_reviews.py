import uuid
from bson import ObjectId
import pytest

BASE = "/api/v1/reviews"

@pytest.mark.asyncio
async def test_reviews_create_get_list_update_delete_and_404s(client):
    film = str(uuid.uuid4())
    author = str(uuid.uuid4())
    stranger = str(uuid.uuid4())

    # create
    r = await client.post(BASE, json={"film_id": film, "text": "hello"}, headers={"X-User-Id": author})
    assert r.status_code == 201
    rid = r.json()["review_id"]

    # get
    r = await client.get(f"{BASE}/{rid}")
    assert r.status_code == 200
    item = r.json()
    assert item["film_id"] == film and item["user_id"] == author and item["text"] == "hello"

    # list by film
    r = await client.get(f"{BASE}/films/{film}?limit=10&offset=0&sort=new")
    assert r.status_code == 200
    lst = r.json()
    assert lst["total"] >= 1
    assert any(i["review_id"] == rid for i in lst["items"])

    # update чужим — 404 (review_not_found_or_not_author)
    r = await client.patch(f"{BASE}/{rid}", json={"text": "x"}, headers={"X-User-Id": stranger})
    assert r.status_code == 404

    # update автором — 200
    r = await client.patch(f"{BASE}/{rid}", json={"text": "world"}, headers={"X-User-Id": author})
    assert r.status_code == 200 and r.json()["ok"] is True

    # delete чужим — 404
    r = await client.delete(f"{BASE}/{rid}", headers={"X-User-Id": stranger})
    assert r.status_code == 404

    # delete автором — 204
    r = await client.delete(f"{BASE}/{rid}", headers={"X-User-Id": author})
    assert r.status_code == 204

    # get после удаления — 404
    r = await client.get(f"{BASE}/{rid}")
    assert r.status_code == 404

    # get для несуществующего корректного ObjectId — 404 (через not_found_if_none)
    rnd = str(ObjectId())
    r = await client.get(f"{BASE}/{rnd}")
    assert r.status_code == 404
