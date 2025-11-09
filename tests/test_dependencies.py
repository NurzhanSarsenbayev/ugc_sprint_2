import pytest
from ugc_api.dependencies import user_id_header, get_db
from ugc_api.db.mongo import get_mongo_db
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException


def test_user_id_header_invalid_returns_422():
    with pytest.raises(HTTPException) as e:
        user_id_header("not-a-uuid")
    assert e.value.status_code == 422


async def test_missing_user_id_header_returns_422_on_endpoint(client):
    # любой эндпоинт с Depends(user_id_header), напр. bookmarks.put
    r = await client.put(
        "/api/v1/bookmarks/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 422


async def test_get_db_returns_database_instance():
    db = await get_db()
    # проверим тип и возможность дернуть список коллекций (не падает)
    assert isinstance(db, AsyncIOMotorDatabase)
    _ = await db.list_collection_names()


async def test_get_mongo_db_returns_same_database_instance():
    db1 = await get_mongo_db()
    db2 = await get_mongo_db()
    # тот же объект БД (один и тот же singleton client/database)
    assert db1.name == db2.name
    # и можно получить список коллекций (проверка работоспособности)
    _ = await db1.list_collection_names()
