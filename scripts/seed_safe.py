import uuid
import os
from app.db import SessionLocal
from app import models
from app.security import hash_api_key


def upsert_api_key(db, tenant_id, name, key_plain, role):
    """
    Cria ou atualiza uma API key. Se já existir com o mesmo nome, atualiza o hash.
    Isso permite regenerar keys mudando apenas a variável de ambiente.
    """
    existing = db.query(models.ApiKey).filter(
        models.ApiKey.tenant_id == tenant_id,
        models.ApiKey.name == name
    ).first()
    
    new_hash = hash_api_key(key_plain)
    
    if existing:
        # Atualiza hash se mudou (permite rotação de keys)
        if existing.key_hash != new_hash:
            existing.key_hash = new_hash
            existing.status = 'active'
            print(f"  ⟳ API key updated: {name} (hash changed)")
        else:
            print(f"  ⊙ API key already exists: {name}")
    else:
        # Cria nova key
        kid = str(uuid.uuid4())
        db.add(models.ApiKey(
            id=kid,
            tenant_id=tenant_id,
            name=name,
            key_hash=new_hash,
            role=role,
            status='active'
        ))
        print(f"  ✓ Created API key: {name}")


def upsert_taxonomy_version(db, tenant_id, version, status='active'):
    """Get or create taxonomy version"""
    existing = db.query(models.TaxonomyVersion).filter_by(
        tenant_id=tenant_id,
        version=version
    ).first()
    
    if existing:
        print(f"  ⊙ Taxonomy version already exists: {version}")
        return existing.id
    
    tv_id = str(uuid.uuid4())
    tv = models.TaxonomyVersion(
        id=tv_id,
        tenant_id=tenant_id,
        version=version,
        status=status
    )
    db.add(tv)
    db.flush()
    print(f"  ✓ Created taxonomy version: {version}")
    return tv_id


def upsert_taxonomy_node(db, node_id, taxonomy_version_id, area, subarea, conceito, descricao, palavras_chave, nivel, critico):
    """Insert taxonomy node only if it doesn't exist (by id)"""
    existing = db.query(models.TaxonomyNode).filter_by(id=node_id).first()
    if not existing:
        node = models.TaxonomyNode(
            id=node_id,
            taxonomy_version_id=taxonomy_version_id,
            area=area,
            subarea=subarea,
            conceito=conceito,
            descricao=descricao,
            palavras_chave=palavras_chave,
            nivel=nivel,
            critico=critico
        )
        db.add(node)
        print(f"  ✓ Created taxonomy node: {node_id} - {conceito}")
    else:
        print(f"  ⊙ Taxonomy node already exists: {node_id}")


def upsert_policy_version(db, tenant_id, version, config):
    """Get or create policy version"""
    existing = db.query(models.PolicyVersion).filter_by(
        tenant_id=tenant_id,
        version=version
    ).first()
    
    if existing:
        print(f"  ⊙ Policy version already exists: {version}")
        return existing.id
    
    pv_id = str(uuid.uuid4())
    pv = models.PolicyVersion(
        id=pv_id,
        tenant_id=tenant_id,
        version=version,
        config=config
    )
    db.add(pv)
    db.flush()
    print(f"  ✓ Created policy version: {version}")
    return pv_id


def upsert_course_binding(db, tenant_id, course_id, taxonomy_version_id, policy_version_id):
    """Insert course binding only if it doesn't exist"""
    existing = db.query(models.CourseBinding).filter_by(
        tenant_id=tenant_id,
        course_id=course_id
    ).first()
    
    if not existing:
        cb_id = str(uuid.uuid4())
        cb = models.CourseBinding(
            id=cb_id,
            tenant_id=tenant_id,
            course_id=course_id,
            taxonomy_version_id=taxonomy_version_id,
            policy_version_id=policy_version_id
        )
        db.add(cb)
        print(f"  ✓ Created course binding: {course_id}")
    else:
        print(f"  ⊙ Course binding already exists: {course_id}")


def run_seed_safe():
    db = SessionLocal()
    try:
        print("=== Starting safe seed ===")
        
        admin_key = os.getenv('ADMIN_API_KEY', 'dev-admin-abc123')
        auditor_key = os.getenv('AUDITOR_API_KEY', 'dev-auditor-abc123')
        client_key = os.getenv('CLIENT_API_KEY', 'dev-client-abc123')
        dvp_key = os.getenv('DVP_API_KEY', 'dvp_live_4PvMicqMbmZ4fQ4LKr4wW3uCe0OeUTPOGO2QMkTPN77S7d1e')

        tenant_id = 'arbe'
        course_id = 'ADM-001'

        # Ensure tenant (merge = upsert)
        print("Setting up tenant...")
        t = models.Tenant(id=tenant_id, name='ARBE', api_key_hash='legacy', status='active')
        db.merge(t)
        db.commit()
        print("  ✓ Tenant ready")

        # API keys
        print("Setting up API keys...")
        upsert_api_key(db, tenant_id, 'dashboard-admin', admin_key, 'admin')
        upsert_api_key(db, tenant_id, 'dashboard-auditor', auditor_key, 'auditor')
        upsert_api_key(db, tenant_id, 'prod-api-client', client_key, 'api-client')
        upsert_api_key(db, tenant_id, 'dvp-live-key', dvp_key, 'admin')
        db.commit()

        # Taxonomy version
        print("Setting up taxonomy...")
        tv_id = upsert_taxonomy_version(db, tenant_id, '2026.01', 'active')
        db.commit()

        # Minimal taxonomy nodes
        print("Setting up taxonomy nodes...")
        upsert_taxonomy_node(
            db, 1101, tv_id,
            area='Administração',
            subarea='Fundamentos',
            conceito='Teorias Administrativas',
            descricao='...',
            palavras_chave=['taylor'],
            nivel='basico',
            critico=False
        )
        db.commit()

        # Policy version
        print("Setting up policy...")
        pv_id = upsert_policy_version(db, tenant_id, 'v3', {'min_score_deferir': 80})
        db.commit()

        # Course binding
        print("Setting up course binding...")
        upsert_course_binding(db, tenant_id, course_id, tv_id, pv_id)
        db.commit()

        print("=== Seed safe completed successfully ===")
    except Exception as e:
        print(f"Error during seed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == '__main__':
    run_seed_safe()
