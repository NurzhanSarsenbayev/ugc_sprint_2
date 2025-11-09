import uuid

async def test_likes_flow(client):
    film = str(uuid.uuid4()); user = str(uuid.uuid4())
    # нет реакции
    r = await client.get(f"/api/v1/likes/{film}", headers={"X-User-Id": user})
    assert r.status_code == 200 and r.json()["value"] is None
    # +1
    r = await client.put(f"/api/v1/likes/{film}", json={"value": 1}, headers={"X-User-Id": user})
    assert r.status_code == 204
    # проверка
    r = await client.get(f"/api/v1/likes/{film}", headers={"X-User-Id": user})
    assert r.json()["value"] == 1
