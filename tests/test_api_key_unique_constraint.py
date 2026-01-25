import uuid
import pytest
from sqlalchemy.exc import IntegrityError

from app.db import SessionLocal
from app.models import ApiKey, Tenant


def test_api_key_key_hash_unique_constraint():
    db = SessionLocal()
    key_hash = f"testkey-{uuid.uuid4().hex}"
    try:
        # ensure tenant exists due to FK constraint
        t = Tenant(id="test-tenant", name="TEST", api_key_hash="x", status="active")
        db.merge(t)
        db.commit()

        a1 = ApiKey(id=str(uuid.uuid4()), tenant_id="test-tenant", name="t1", key_hash=key_hash, role="api-client")
        db.add(a1)
        db.commit()

        a2 = ApiKey(id=str(uuid.uuid4()), tenant_id="test-tenant", name="t2", key_hash=key_hash, role="api-client")
        db.add(a2)
        with pytest.raises(IntegrityError):
            db.commit()
    finally:
        # cleanup any leftover records
        try:
            db.rollback()
            db.query(ApiKey).filter(ApiKey.key_hash == key_hash).delete()
            db.query(Tenant).filter(Tenant.id == 'test-tenant').delete()
            db.commit()
        finally:
            db.close()
