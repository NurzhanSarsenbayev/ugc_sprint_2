import os
import pytest
from httpx import AsyncClient, ASGITransport
from asgi_lifespan import LifespanManager
from motor.motor_asyncio import AsyncIOMotorClient

from ugc_api.main import app
from ugc_api.core.config import settings


@pytest.fixture(scope="session", autouse=True)
def test_env():
    os.environ["MONGO_DSN"] =\
        "mongodb://mongo:27017/engagement_test?replicaSet=rs0"
    os.environ["SENTRY_DSN"] = ""  # отключаем Sentry
    settings.mongo_dsn = os.environ["MONGO_DSN"]
    settings.sentry_dsn = ""


@pytest.fixture(scope="session")
async def client():
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport,
                               base_url="http://test") as ac:
            yield ac


@pytest.fixture(autouse=True)
async def clean_db():
    """Чистим коллекции тестовой Mongo между тестами."""
    dsn = settings.mongo_dsn
    db_name = dsn.split("/")[-1].split("?")[0]
    client = AsyncIOMotorClient(dsn)
    db = client[db_name]
    for name in await db.list_collection_names():
        await db[name].delete_many({})
    yield
    client.close()
