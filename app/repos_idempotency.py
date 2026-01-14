from sqlalchemy.orm import Session
from sqlalchemy import select
from app import models

def get_existing_result(db: Session, tenant_id: str, request_id: str):
    return db.execute(
        select(models.EquivalenceResult).where(
            models.EquivalenceResult.tenant_id == tenant_id,
            models.EquivalenceResult.request_id == request_id
        )
    ).scalar_one_or_none()
