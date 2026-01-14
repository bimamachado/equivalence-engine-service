from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.repos import JobRepo
from app.queue import dead_queue

def on_job_failure(job, connection, type, value, traceback):
    """
    job.args deve conter: (job_id, item_id)
    """
    job_id = None
    item_id = None
    try:
        if job.args and len(job.args) >= 2:
            job_id, item_id = job.args[0], job.args[1]
    except Exception:
        pass

    db: Session = SessionLocal()
    try:
        if item_id:
            # Marca item como failed
            JobRepo().mark_item(db, item_id, "failed", error=str(value))

        if job_id:
            JobRepo().update_counts(db, job_id, failed_inc=1)

        # Empurra para DLQ com contexto mínimo
        dead_queue.enqueue(
            "app.worker.reprocess_dead_item",
            job_id,
            item_id,
            str(value),
            job.id,
            job.retries_left if hasattr(job, "retries_left") else None,
        )
    finally:
        db.close()


def on_job_success(job, connection, result, *args, **kwargs):
    # Optional: aqui você poderia registrar métricas, etc.
    return
