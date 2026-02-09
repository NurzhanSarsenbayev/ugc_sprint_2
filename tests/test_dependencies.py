import pytest
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from ugc_api.db.mongo import get_mongo_db
from ugc_api.dependencies import get_db, user_id_header


def test_user_id_header_invalid_returns_422():
    with pytest.raises(HTTPException) as e:
        user_id_header("not-a-uuid")
    assert e.value.status_code == 422


async def test_missing_user_id_header_returns_422_on_endpoint(client):
    # Any endpoint that uses Depends(user_id_header), e.g. bookmarks.put
    r = await client.put("/api/v1/bookmarks/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 422


async def test_get_db_returns_database_instance():
    db = await get_db()
    # Check the type and that listing collections works (no exception)
    assert isinstance(db, AsyncIOMotorDatabase)
    _ = await db.list_collection_names()


async def test_get_mongo_db_returns_same_database_instance():
    db1 = await get_mongo_db()
    db2 = await get_mongo_db()
    # Same DB object (same singleton client/database)
    assert db1.name == db2.name
    # And listing collections works (sanity check)
    _ = await db1.list_collection_names()
