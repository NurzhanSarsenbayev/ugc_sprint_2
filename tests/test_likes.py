"""Tests for likes API flows and film stats updates."""

from __future__ import annotations

from tests.helpers import new_film, new_user, read_stats, uid_header


async def test_like_initial_value_is_none(client):
    film, user = new_film(), new_user()

    r = await client.get(
        f"/api/v1/likes/{film}",
        headers=uid_header(user),
    )
    assert r.status_code == 200
    assert r.json()["value"] is None


async def test_put_like_sets_value_1_returns_204(client):
    film, user = new_film(), new_user()

    r = await client.put(
        f"/api/v1/likes/{film}",
        json={"value": 1},
        headers=uid_header(user),
    )
    assert r.status_code == 204


async def test_like_transitions_plus1_to_minus1_affect_stats(client):
    film, user = new_film(), new_user()

    await client.put(
        f"/api/v1/likes/{film}",
        json={"value": 1},
        headers=uid_header(user),
    )
    await client.put(
        f"/api/v1/likes/{film}",
        json={"value": -1},
        headers=uid_header(user),
    )

    s = await read_stats(client, film)
    assert s["likes"] == 0
    assert s["dislikes"] == 1


async def test_delete_like_removes_reaction_returns_204(client):
    film, user = new_film(), new_user()

    await client.put(
        f"/api/v1/likes/{film}",
        json={"value": 1},
        headers=uid_header(user),
    )
    r = await client.delete(
        f"/api/v1/likes/{film}",
        headers=uid_header(user),
    )
    assert r.status_code == 204


async def test_delete_like_without_existing_reaction_returns_204(client):
    film, user = new_film(), new_user()

    # Deleting without any prior like/dislike should still be OK.
    r = await client.delete(
        f"/api/v1/likes/{film}",
        headers=uid_header(user),
    )
    assert r.status_code == 204
