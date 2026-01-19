import uuid
import os
from app.db import SessionLocal
from app import models
from app.security import hash_api_key


def upsert_key_local(db, tenant_id, name, key_plain, role):
    kid = str(uuid.uuid4())
    db.add(models.ApiKey(id=kid, tenant_id=tenant_id, name=name, key_hash=hash_api_key(key_plain), role=role, status='active'))


def run_seed_safe():
    db = SessionLocal()
    try:
        admin_key = os.getenv('ADMIN_API_KEY', 'dev-admin-abc123')
        auditor_key = os.getenv('AUDITOR_API_KEY', 'dev-auditor-abc123')
        client_key = os.getenv('CLIENT_API_KEY', 'dev-client-abc123')

        tenant_id = 'arbe'
        course_id = 'ADM-001'

        # Ensure tenant
        t = models.Tenant(id=tenant_id, name='ARBE', api_key_hash='legacy', status='active')
        db.merge(t)
        db.commit()

        # API keys
        upsert_key_local(db, tenant_id, 'dashboard-admin', admin_key, 'admin')
        upsert_key_local(db, tenant_id, 'dashboard-auditor', auditor_key, 'auditor')
        upsert_key_local(db, tenant_id, 'prod-api-client', client_key, 'api-client')
        db.commit()

        # Taxonomy version
        tv_id = str(uuid.uuid4())
        tv = models.TaxonomyVersion(id=tv_id, tenant_id=tenant_id, version='2026.01', status='active')
        db.add(tv)
        db.commit()

        # Minimal taxonomy nodes
        nodes = [
            models.TaxonomyNode(id=1101, taxonomy_version_id=tv_id, area='Administração', subarea='Fundamentos', conceito='Teorias Administrativas', descricao='...', palavras_chave=['taylor'], nivel='basico', critico=False),
        ]
        for n in nodes:
            db.add(n)
        db.commit()

        # Policy version
        pv_id = str(uuid.uuid4())
        pv = models.PolicyVersion(id=pv_id, tenant_id=tenant_id, version='v3', config={'min_score_deferir': 80})
        db.add(pv)
        db.commit()

        # Course binding
        cb_id = str(uuid.uuid4())
        cb = models.CourseBinding(id=cb_id, tenant_id=tenant_id, course_id=course_id, taxonomy_version_id=tv_id, policy_version_id=pv_id)
        db.add(cb)
        db.commit()

        print('Seed safe completed')
    finally:
        db.close()


if __name__ == '__main__':
    run_seed_safe()
