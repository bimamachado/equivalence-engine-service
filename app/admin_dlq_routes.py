from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.deps import require_role
from app import models
from app.queue import queue, default_retry
from app.rq_hooks import on_job_failure, on_job_success

router = APIRouter(prefix="/admin/dlq", dependencies=[Depends(require_role("admin"))])

@router.post("/requeue/{item_id}")
def requeue_item(item_id: str, db: Session = Depends(get_db)):
    item = db.get(models.JobItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="JobItem not found")

    # requeue só se estiver failed
    if item.status != "failed":
        raise HTTPException(status_code=400, detail=f"Item status must be failed, got {item.status}")

    # marca como queued e limpa erro
    item.status = "queued"
    item.error = None
    db.commit()

    # enfileira de novo
    job_id = item.job_id
    queue.enqueue(
        "app.worker.process_job_item",
        job_id,
        item.id,
        retry=default_retry(),
        on_failure=on_job_failure,
        on_success=on_job_success,
        job_timeout=300
    )

    return {"ok": True, "item_id": item.id, "job_id": job_id}
