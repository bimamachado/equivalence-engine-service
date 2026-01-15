import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app import models
from app.queue import queue
from app.deps import get_tenant_id

router = APIRouter(prefix="/admin", dependencies=[Depends(require_role("admin"))])

@router.post("/taxonomy_versions")
def create_taxonomy_version(payload: dict, tenant_id: str = Depends(get_tenant_id), db: Session = Depends(get_db)):
    """
    payload:
      { tenant_id, version, nodes:[{id,area,subarea,conceito,descricao,palavras_chave,nivel,critico}] }
    """
    version = payload["version"]
    nodes = payload.get("nodes", [])

    tv_id = str(uuid.uuid4())
    tv = models.TaxonomyVersion(id=tv_id, tenant_id=tenant_id, version=version, status="active")
    db.add(tv)

    for n in nodes:
        db.add(models.TaxonomyNode(
            id=int(n["id"]),
            taxonomy_version_id=tv_id,
            area=n["area"], subarea=n["subarea"],
            conceito=n["conceito"], descricao=n["descricao"],
            palavras_chave=n.get("palavras_chave", []),
            nivel=n.get("nivel", "basico"),
            critico=bool(n.get("critico", False))
        ))
    db.commit()

    # Enfileira build do index (embeddings)
    queue.enqueue("app.index_builder.build_taxonomy_index", tenant_id, version)

    return {"taxonomy_version_id": tv_id, "tenant_id": tenant_id, "version": version, "nodes": len(nodes), "index_job": "queued"}

@router.post("/policy_versions")
def create_policy_version(payload: dict, tenant_id: str = Depends(get_tenant_id), db: Session = Depends(get_db)):
    """
    payload: { tenant_id, version, config:{...} }
    """
    pid = str(uuid.uuid4())
    pv = models.PolicyVersion(id=pid, tenant_id=tenant_id, version=payload["version"], config=payload["config"])
    db.add(pv)
    db.commit()
    return {"policy_version_id": pid, "tenant_id": pv.tenant_id, "version": pv.version}

@router.post("/bindings")
def bind_course(payload: dict, tenant_id: str = Depends(get_tenant_id), db: Session = Depends(get_db)):
    """
    payload: { tenant_id, course_id, taxonomy_version, policy_version }
    """
    tv = db.query(models.TaxonomyVersion).filter(
        models.TaxonomyVersion.tenant_id == tenant_id,
        models.TaxonomyVersion.version == payload["taxonomy_version"]
    ).one()

    pv = db.query(models.PolicyVersion).filter(
        models.PolicyVersion.tenant_id == tenant_id,
        models.PolicyVersion.version == payload["policy_version"]
    ).one()

    bid = str(uuid.uuid4())
    b = models.CourseBinding(
        id=bid,
        tenant_id=tenant_id,
        course_id=payload["course_id"],
        taxonomy_version_id=tv.id,
        policy_version_id=pv.id
    )
    db.add(b)
    db.commit()
    return {"binding_id": bid, "tenant_id": b.tenant_id, "course_id": b.course_id}
