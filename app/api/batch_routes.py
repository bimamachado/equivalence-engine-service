import uuid
from fastapi import APIRouter, Depends
from app.deps import get_tenant_id
from sqlalchemy.orm import Session
from app.db import get_db
from app.queue import queue
from app import models
from app.repos import JobRepo
from app.queue import queue, default_retry
from app.rq_hooks import on_job_failure, on_job_success
router = APIRouter()



@router.post("/v1/equivalences/batch")
def create_batch(payload: dict, tenant_id: str = Depends(get_tenant_id), db: Session = Depends(get_db)):
    """
    payload esperado:
      { "items": [ <EvaluateRequest JSON>, <EvaluateRequest JSON>, ... ] }
    """
    items = payload.get("items", [])
    job_id = str(uuid.uuid4())

    job = models.Job(id=job_id, tenant_id=tenant_id, status="queued", total=len(items), done=0, failed=0)
    job_items = []
    for it in items:
         # sanitize payload: never trust tenant_id coming from client
        if isinstance(it, dict):
            item_payload = dict(it)
            item_payload.pop("tenant_id", None)
        else:
          item_payload = it

        item_id = str(uuid.uuid4())
        job_items.append(models.JobItem(id=item_id, job_id=job_id, status="queued", payload=item_payload))
    JobRepo().create_job(db, job, job_items)

    # enfileira cada item
    for ji in job_items:
        queue.enqueue("app.worker.process_job_item", job_id, ji.id)

    return {"job_id": job_id, "status": "QUEUED", "total": len(items)}

@router.get("/v1/jobs/{job_id}")
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.get(models.Job, job_id)
    return {
        "job_id": job.id,
        "tenant_id": job.tenant_id,
        "status": job.status,
        "progress": {"done": job.done, "failed": job.failed, "total": job.total}
    }

@router.get("/v1/jobs/{job_id}/results")
def get_job_results(job_id: str, db: Session = Depends(get_db)):
    items = db.query(models.JobItem).filter(models.JobItem.job_id == job_id).all()
    return [
        {"item_id": it.id, "status": it.status, "result_id": it.result_id, "error": it.error}
        for it in items
    ]
