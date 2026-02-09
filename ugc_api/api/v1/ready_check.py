from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from ugc_api.dependencies import get_db

from ugc_api.db.redis import redis_ping
router = APIRouter(tags=["readiness"])


@router.get("/ready")
async def readiness(db=Depends(get_db)):
    mongo_ok = True
    try:
        await db.command("ping")
    except Exception:
        mongo_ok = False

    redis_ok = await redis_ping()

    if mongo_ok and redis_ok:
        return {"status": "ready"}

    return JSONResponse(
        {"status": "not ready", "mongo": mongo_ok, "redis": redis_ok},
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
    )
