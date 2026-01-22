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

        # Salva resultado em EquivalenceResult e marca item como concluído
        try:
            import uuid as _uuid
            from app.repos import ResultRepo

            result_id = str(_uuid.uuid4())
            origem_nome = payload.get("origem", {}).get("nome")
            origem_carga = payload.get("origem", {}).get("carga_horaria")
            destino_nome = payload.get("destino", {}).get("nome")
            destino_carga = payload.get("destino", {}).get("carga_horaria")

            # cria modelo de EquivalenceResult compatível com app.models.EquivalenceResult
            r = models.EquivalenceResult(
                id=result_id,
                request_id=request_id,
                tenant_id=tenant_id,
                course_id=None,
                origem_nome=origem_nome or "",
                origem_carga=origem_carga or 0,
                origem_hash=sha256_text(payload.get("origem", {}).get("ementa", "")),
                destino_nome=destino_nome or "",
                destino_carga=destino_carga or 0,
                destino_hash=sha256_text(payload.get("destino", {}).get("ementa", "")),
                decision=(resp.decisao if hasattr(resp, 'decisao') else getattr(resp, 'decision', None) or ""),
                score=(resp.score if hasattr(resp, 'score') else 0),
                breakdown=(resp.breakdown.model_dump() if hasattr(resp, 'breakdown') and hasattr(resp.breakdown, 'model_dump') else (resp.breakdown if hasattr(resp, 'breakdown') else {})),
                missing=(resp.faltantes if hasattr(resp, 'faltantes') else (resp.missing if hasattr(resp, 'missing') else [])),
                missing_critical=(resp.criticos_faltantes if hasattr(resp, 'criticos_faltantes') else (resp.missing_critical if hasattr(resp, 'missing_critical') else [])),
                justificativa_curta=(resp.justificativa_curta if hasattr(resp, 'justificativa_curta') else (resp.short_justification if hasattr(resp, 'short_justification') else "")),
                justificativa_detalhada=(resp.justificativa_detalhada if hasattr(resp, 'justificativa_detalhada') else (resp.long_justification if hasattr(resp, 'long_justification') else "")),
                degraded_mode=(resp.degraded_mode if hasattr(resp, 'degraded_mode') else False),
                model_version=(resp.model_version if hasattr(resp, 'model_version') else ""),
                policy_version=(resp.policy_version if hasattr(resp, 'policy_version') else ""),
                taxonomy_version=(resp.taxonomy_version if hasattr(resp, 'taxonomy_version') else ""),
                timings_ms=(resp.timings_ms.model_dump() if hasattr(resp, 'timings_ms') and hasattr(resp.timings_ms, 'model_dump') else (resp.timings_ms if hasattr(resp, 'timings_ms') else {})),
            )

            # salva no DB
            ResultRepo().save_result(db, r)

            # marca item com result_id e atualiza contadores
            repo.mark_item(db, item_id, "done", result_id=result_id)
            repo.update_counts(db, job_id, done_inc=1)

            # se job completo, marca status
            job_obj = db.get(models.Job, job_id)
            if job_obj and (job_obj.done + job_obj.failed) >= (job_obj.total or 0):
                job_obj.status = "done"
                db.commit()

        except Exception as e:
            # em caso de erro ao salvar resultado, marca item como failed
            repo.mark_item(db, item_id, "failed", error=str(e))
            repo.update_counts(db, job_id, failed_inc=1)
            return

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