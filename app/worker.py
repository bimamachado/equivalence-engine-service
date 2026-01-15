import uuid
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.repos import JobRepo
from app import db, models
from app.engine.service import EquivalenceEngine
from app.engine.utils import sha256_text
from app.locks import acquire_lock, release_lock, lock_key
from app.repos_idempotency import get_existing_result

# TODO: aqui você constrói seu engine com repos/mapper real.
# Para MVP: reaproveite seu get_engine() e importe dentro.
from app.api.routes import get_engine

def process_job_item(job_id: str, item_id: str):
    db: Session = SessionLocal()
    repo = JobRepo()
    lock = None
    try:
        item = db.get(models.JobItem, item_id)
        payload = item.payload

# tenant_id is taken from the enclosing Job (trusted), not from client payload
        job = db.get(models.Job, job_id)
        tenant_id = job.tenant_id
        request_id = payload.get("request_id")
        # Se não veio request_id, você pode gerar aqui, mas para batch é ideal vir
        if not request_id:
            request_id = str(uuid.uuid4())
            payload["request_id"] = request_id
            item.payload = payload
            db.commit()

        # 1) Idempotência: se já existe, marca done e associa
        existing = get_existing_result(db, tenant_id, request_id)
        if existing:
            repo.mark_item(db, item_id, "done", result_id=existing.id)
            repo.update_counts(db, job_id, done_inc=1)
            return

        # 2) Lock anti-dupla execução
        lock = lock_key(tenant_id, request_id)
        if not acquire_lock(lock, ttl_seconds=360):
            # outro worker está processando
            repo.mark_item(db, item_id, "queued")
            return

        repo.mark_item(db, item_id, "running")

        engine: EquivalenceEngine = get_engine()
        from app.api.schemas import EvaluateRequest
        req = EvaluateRequest(**payload)

        resp = engine.evaluate(req, tenant_id)

        # salva resultado com constraint unique (tenant_id, request_id)
        # ... seu bloco de save já existente ...
        # se der violação, você trata abaixo

    except Exception as e:
        # Se for erro de unique constraint, tenta buscar existente e marcar done
        try:
            tenant_id = tenant_id if 'tenant_id' in locals() else None
            request_id = request_id if 'request_id' in locals() else None
            if tenant_id and request_id:
                existing = get_existing_result(db, tenant_id, request_id)
                if existing:
                    repo.mark_item(db, item_id, "done", result_id=existing.id)
                    repo.update_counts(db, job_id, done_inc=1)
                    return
        except Exception:
            pass

        repo.mark_item(db, item_id, "failed", error=str(e))
        repo.update_counts(db, job_id, failed_inc=1)

    finally:
        if lock:
            release_lock(lock)
        db.close()

def reprocess_dead_item(job_id: str, item_id: str, reason: str, failed_job_id: str, retries_left):
    """
    Função chamada pela DLQ. Não reprocessa automaticamente.
    Serve para registrar e deixar pronto para ação humana.
    """
    db: Session = SessionLocal()
    try:
        # marca como "dead" para auditoria interna
        if item_id:
            item = db.get(models.JobItem, item_id)
            if item:
                item.status = "failed"
                item.error = f"[DLQ] reason={reason} failed_job_id={failed_job_id}"
                db.commit()
        return {"ok": True}
    finally:
        db.close()