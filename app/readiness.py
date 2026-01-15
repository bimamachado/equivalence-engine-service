from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from app.db import engine
from app.redis_client import redis_conn

router = APIRouter()

@router.get("/ready")
def readiness():
    try:
        # DB
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        # Redis
        redis_conn.ping()

    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

    return {"status": "ready"}
