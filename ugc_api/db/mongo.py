from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from ugc_api.core.config import settings
import logging

_client: AsyncIOMotorClient | None = None


async def get_client() -> AsyncIOMotorClient:
    """
    Singleton Motor client with explicit timeouts and connection pool settings.
    """
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(
            settings.mongo_dsn,
            appname="ugc-engagement-api",
            tz_aware=True,  # ensure created_at is timezone-aware
            uuidRepresentation="standard",
            maxPoolSize=50,
            minPoolSize=0,
            serverSelectionTimeoutMS=3000,
            connectTimeoutMS=3000,
            socketTimeoutMS=5000,
            retryWrites=True,
        )
        # quick connectivity check (do not block startup longer than timeout)
        try:
            await _client.admin.command("ping")
        except Exception as e:
            logging.getLogger(__name__).warning(
                "mongo_ping_failed", extra={"err": str(e)}
            )
    return _client


async def get_mongo_db() -> AsyncIOMotorDatabase:
    client = await get_client()
    return client[settings.mongo_db]


async def get_collection(name: str):
    db = await get_mongo_db()
    return db[name]


async def close_client() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None
