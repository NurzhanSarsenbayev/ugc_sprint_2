import pytest
from tests.helpers import new_user, new_film, uid_header

BASE = "/api/v1/bookmarks"

@pytest.mark.asyncio
async def test_bookmark_create_returns_created_true(client):
    user, film = new_user(), new_film()
    r = await client.put(f"{BASE}/{film}", headers=uid_header(user))
    assert r.status_code == 200 and r.json() == {"ok": True, "created": True}

@pytest.mark.asyncio
async def test_bookmark_put_twice_created_flag_toggles(client):
    user, film = new_user(), new_film()
    await client.put(f"{BASE}/{film}", headers=uid_header(user))
    r = await client.put(f"{BASE}/{film}", headers=uid_header(user))
    assert r.status_code == 200 and r.json() == {"ok": True, "created": False}

@pytest.mark.asyncio
async def test_bookmarks_pagination_pages_do_not_overlap(client):
    user = new_user()
    films = [new_film() for _ in range(5)]
    for fid in films:
        await client.put(f"{BASE}/{fid}", headers=uid_header(user))

    r1 = await client.get(f"{BASE}?limit=2&offset=0", headers=uid_header(user))
    r2 = await client.get(f"{BASE}?limit=2&offset=2", headers=uid_header(user))

    ids1 = {i["film_id"] for i in r1.json()["items"]}
    ids2 = {i["film_id"] for i in r2.json()["items"]}
    assert ids1.isdisjoint(ids2)

@pytest.mark.asyncio
async def test_bookmark_delete_then_delete_again_deleted_false(client):
    user, film = new_user(), new_film()
    await client.put(f"{BASE}/{film}", headers=uid_header(user))
    r1 = await client.delete(f"{BASE}/{film}", headers=uid_header(user))
    r2 = await client.delete(f"{BASE}/{film}", headers=uid_header(user))
    assert r1.json() == {"ok": True, "deleted": True} and r2.json() == {"ok": True, "deleted": False}

