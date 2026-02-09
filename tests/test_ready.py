import pytest


@pytest.mark.asyncio
async def test_ready_returns_503_if_redis_down(client, monkeypatch):
    async def fake_redis_ping() -> bool:
        return False

    monkeypatch.setattr("ugc_api.api.v1.ready_check.redis_ping", fake_redis_ping)

    r = await client.get("/ready")
    assert r.status_code == 503
    data = r.json()
    assert data["status"] == "not ready"
    assert data["redis"] is False
