from pathlib import Path
# paths (WSL UNC)
batch_path = r"\\\\wsl.localhost\\Ubuntu-24.04\\home\\amachado\\workspace\\equivalence-engine-service\\app\\api\\batch_routes.py"
worker_path = r"\\\\wsl.localhost\\Ubuntu-24.04\\home\\amachado\\workspace\\equivalence-engine-service\\app\\worker.py"

# Update batch_routes.py
p = Path(batch_path)
s = p.read_text()
old_block = (
    "queue.enqueue(\n"
    "    \"app.worker.process_job_item\",\n"
    "    job_id,\n"
    "    ji.id,\n"
    "    retry=default_retry(),\n"
    "    on_failure=on_job_failure,\n"
    "    on_success=on_job_success,\n"
    "    job_timeout=300  # 5 minutos por item (ajuste)\n"
    ")\n\n"
)
if old_block in s:
    s = s.replace(old_block, "")

s = s.replace(
    'for it in items:\n        item_id = str(uuid.uuid4())\n        job_items.append(models.JobItem(id=item_id, job_id=job_id, status="queued", payload=it))',
    'for it in items:\n        # sanitize payload: never trust tenant_id coming from client\n        if isinstance(it, dict):\n            item_payload = dict(it)\n            item_payload.pop("tenant_id", None)\n        else:\n            item_payload = it\n\n        item_id = str(uuid.uuid4())\n        job_items.append(models.JobItem(id=item_id, job_id=job_id, status="queued", payload=item_payload))'
)

p.write_text(s)

# Update worker.py
pw = Path(worker_path)
sw = pw.read_text()
if 'tenant_id = payload.get("tenant_id")' in sw:
    sw = sw.replace(
        '        tenant_id = payload.get("tenant_id")  # MAS: em produ\xc3\xa7\xc3\xa3o, voc\xc3\xaa deveria gravar tenant no job/item, n\xc3\xa3o confiar no payload',
        '        # tenant_id is taken from the enclosing Job, not from client payload\n        job = db.get(models.Job, job_id)\n        tenant_id = job.tenant_id'
    )

sw = sw.replace('        resp = engine.evaluate(req)\n', '        resp = engine.evaluate(req, tenant_id)\n')

pw.write_text(sw)

print('Patcheado: batch_routes.py e worker.py')
