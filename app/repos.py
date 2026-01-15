from sqlalchemy.orm import Session
from sqlalchemy import select, update
from app import models

class TaxonomyRepo:
    def get_nodes(self, db: Session, tenant_id: str, version: str):
        tv = db.execute(
            select(models.TaxonomyVersion).where(
                models.TaxonomyVersion.tenant_id == tenant_id,
                models.TaxonomyVersion.version == version
            )
        ).scalar_one()
        nodes = db.execute(
            select(models.TaxonomyNode).where(models.TaxonomyNode.taxonomy_version_id == tv.id)
        ).scalars().all()
        return tv, nodes

class PolicyRepo:
    def get_policy(self, db: Session, tenant_id: str, version: str):
        return db.execute(
            select(models.PolicyVersion).where(
                models.PolicyVersion.tenant_id == tenant_id,
                models.PolicyVersion.version == version
            )
        ).scalar_one()

    def resolve_binding(self, db: Session, tenant_id: str, course_id: str):
        b = db.execute(
            select(models.CourseBinding).where(
                models.CourseBinding.tenant_id == tenant_id,
                models.CourseBinding.course_id == course_id
            ).order_by(models.CourseBinding.active_from.desc())
        ).scalar_one()
        return b

class ResultRepo:
    def save_result(self, db: Session, r: models.EquivalenceResult):
        db.add(r)
        db.commit()
        return r

class JobRepo:
    def create_job(self, db: Session, job: models.Job, items: list[models.JobItem]):
        db.add(job)
        for it in items:
            db.add(it)
        db.commit()

    def update_counts(self, db: Session, job_id: str, done_inc=0, failed_inc=0, status=None):
        job = db.get(models.Job, job_id)
        job.done += done_inc
        job.failed += failed_inc
        if status:
            job.status = status
        db.commit()

    def mark_item(self, db: Session, item_id: str, status: str, result_id: str | None = None, error: str | None = None):
        item = db.get(models.JobItem, item_id)
        item.status = status
        item.result_id = result_id
        item.error = error
        db.commit()
