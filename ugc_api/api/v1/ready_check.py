from fastapi import APIRouter, Depends
from ugc_api.dependencies import get_db

router = APIRouter(tags=["readiness"])

@router.get("/ready")
async def readiness(db = Depends(get_db)):
    try:
        await db.command("ping")
        return {"status": "ready"}
    except Exception:
        return {"status": "not ready"}
