from app.db import SessionLocal
from app.tuning import tune_for_course, create_policy_version
from app import models
import uuid

def run(tenant_id: str, course_id: str, new_version: str):
    db = SessionLocal()
    try:
        best = tune_for_course(db, tenant_id, course_id)

        # pega policy atual do binding
        b = db.query(models.CourseBinding).filter(
            models.CourseBinding.tenant_id == tenant_id,
            models.CourseBinding.course_id == course_id
        ).order_by(models.CourseBinding.active_from.desc()).one()

        current_policy = db.get(models.PolicyVersion, b.policy_version_id).config

        tuned = dict(current_policy)
        tuned["min_score_deferir"] = best["min_score_deferir"]
        tuned["min_score_complemento"] = best["min_score_complemento"]
        tuned["tuning_accuracy"] = best["accuracy"]
        tuned["tuned_for_course"] = course_id

        pv = create_policy_version(db, tenant_id, base_version="N/A", new_version=new_version, config=tuned)

        # cria novo binding usando mesma taxonomia
        bid = str(uuid.uuid4())
        db.add(models.CourseBinding(
            id=bid, tenant_id=tenant_id, course_id=course_id,
            taxonomy_version_id=b.taxonomy_version_id,
            policy_version_id=pv.id
        ))
        db.commit()

        print("Tuning OK:", best, "new_policy_version:", new_version)
    finally:
        db.close()

if __name__ == "__main__":
    # exemplo
    run("arbe", "ADM-001", "v3-ADM-001-tuned-01")
