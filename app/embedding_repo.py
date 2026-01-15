import json
from sqlalchemy.orm import Session
from sqlalchemy import select
from app import models
from app.redis_client import redis_conn
from app.config import settings

def _redis_key_text(tenant_id: str, taxonomy_version_id: str, text_hash: str) -> str:
    return f"emb:text:{tenant_id}:{taxonomy_version_id}:{text_hash}"

class EmbeddingRepo:
    def get_text_embedding(self, db: Session, tenant_id: str, taxonomy_version_id: str, text_hash: str):
        key = _redis_key_text(tenant_id, taxonomy_version_id, text_hash)
        cached = redis_conn.get(key)
        if cached:
            return json.loads(cached.decode("utf-8"))

        row = db.execute(
            select(models.TextEmbedding).where(
                models.TextEmbedding.tenant_id == tenant_id,
                models.TextEmbedding.taxonomy_version_id == taxonomy_version_id,
                models.TextEmbedding.text_hash == text_hash
            )
        ).scalar_one_or_none()

        if row:
            redis_conn.setex(key, settings.EMBEDDING_CACHE_TTL, json.dumps(row.vector).encode("utf-8"))
            return row.vector

        return None

    def save_text_embedding(self, db: Session, tenant_id: str, taxonomy_version_id: str, text_hash: str, vector: list[float]):
        row = models.TextEmbedding(
            tenant_id=tenant_id,
            taxonomy_version_id=taxonomy_version_id,
            text_hash=text_hash,
            vector=vector
        )
        db.add(row)
        db.commit()

        key = _redis_key_text(tenant_id, taxonomy_version_id, text_hash)
        redis_conn.setex(key, settings.EMBEDDING_CACHE_TTL, json.dumps(vector).encode("utf-8"))

    def get_taxonomy_vectors(self, db: Session, taxonomy_version_id: str):
        # MVP: carrega tudo do DB (ok para taxonomia pequena/média)
        rows = db.query(models.TaxonomyEmbedding).filter(models.TaxonomyEmbedding.taxonomy_version_id == taxonomy_version_id).all()
        return {r.node_id: r.vector for r in rows}
