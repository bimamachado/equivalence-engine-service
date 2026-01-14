from sqlalchemy.orm import Session
from app.repos import PolicyRepo
from app import models

def resolve_versions(db: Session, tenant_id: str, course_id: str | None, taxonomy_version: str | None, policy_version: str | None):
    # 1) Se veio explicitamente, usa
    if taxonomy_version and policy_version:
        tv = db.query(models.TaxonomyVersion).filter(
            models.TaxonomyVersion.tenant_id == tenant_id,
            models.TaxonomyVersion.version == taxonomy_version
        ).one()
        pv = db.query(models.PolicyVersion).filter(
            models.PolicyVersion.tenant_id == tenant_id,
            models.PolicyVersion.version == policy_version
        ).one()
        return tv, pv

    # 2) Se veio course_id, resolve binding ativo
    if course_id:
        b = PolicyRepo().resolve_binding(db, tenant_id, course_id)
        tv = db.get(models.TaxonomyVersion, b.taxonomy_version_id)
        pv = db.get(models.PolicyVersion, b.policy_version_id)
        return tv, pv

    raise ValueError("Forneça (taxonomy_version + policy_version) ou course_id.")
