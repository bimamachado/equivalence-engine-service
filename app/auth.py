from sqlalchemy.orm import Session
from sqlalchemy import select
from app import models
from app.security import hash_api_key

def get_api_key_record(db: Session, api_key: str) -> models.ApiKey | None:
    key_hash = hash_api_key(api_key)

    rec = db.execute(
        select(models.ApiKey).where(models.ApiKey.key_hash == key_hash)
    ).scalar_one_or_none()

    if not rec:
        return None
    if rec.status != "active":
        return None

    tenant = db.get(models.Tenant, rec.tenant_id)
    if not tenant or tenant.status != "active":
        return None

    return rec
