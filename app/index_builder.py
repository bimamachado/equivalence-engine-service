from sqlalchemy.orm import Session
from app.db import SessionLocal
from app import models
from app.mapper.taxonomy_index import build_taxonomy_text

from app.mapper.clients import HttpClientConfig, SimpleHttpEmbeddingClient
import os

def build_taxonomy_index(tenant_id: str, taxonomy_version: str):
    db: Session = SessionLocal()
    try:
        tv = db.query(models.TaxonomyVersion).filter(
            models.TaxonomyVersion.tenant_id == tenant_id,
            models.TaxonomyVersion.version == taxonomy_version
        ).one()

        nodes = db.query(models.TaxonomyNode).filter(models.TaxonomyNode.taxonomy_version_id == tv.id).all()
        if not nodes:
            return {"ok": False, "reason": "no_nodes"}

        texts = []
        for n in nodes:
            tmp = type("N", (), {
                "area": n.area, "subarea": n.subarea, "conceito": n.conceito,
                "descricao": n.descricao, "palavras_chave": n.palavras_chave
            })()
            texts.append(build_taxonomy_text(tmp))

        embed_cfg = HttpClientConfig(base_url=os.getenv("EMBED_URL", "http://localhost:9001"))
        embedder = SimpleHttpEmbeddingClient(embed_cfg, path="/embed")
        vectors = embedder.embed(texts)

        db.query(models.TaxonomyEmbedding).filter(models.TaxonomyEmbedding.taxonomy_version_id == tv.id).delete()
        db.commit()

        for node, vec in zip(nodes, vectors):
            db.add(models.TaxonomyEmbedding(taxonomy_version_id=tv.id, node_id=node.id, vector=vec))
        db.commit()

        return {"ok": True, "taxonomy_version": taxonomy_version, "count": len(nodes)}
    finally:
        db.close()
