from __future__ import annotations
from app.engine.service import EquivalenceEngine
import uuid
from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from app.db import get_db
from app.deps import get_tenant_id
from app.repos_idempotency import get_existing_result
from app.api.schemas import EvaluateRequest
from app.engine.service import EquivalenceEngine
router = APIRouter()

_ENGINE_SINGLETON: EquivalenceEngine | None = None

def get_engine() -> EquivalenceEngine:
    global _ENGINE_SINGLETON
    if _ENGINE_SINGLETON is not None:
        return _ENGINE_SINGLETON

    from app.taxonomy.store import TaxonomyStore
    from app.taxonomy.models import TaxonomyNode
    from app.cache.cache import SimpleTTLCache
    from app.audit.repository import AuditRepository

    # Clients
    from app.mapper.clients import HttpClientConfig, SimpleHttpEmbeddingClient, SimpleHttpLLMJsonClient
    from app.mapper.taxonomy_index import build_index
    from app.mapper.embedding_llm_mapper import EmbeddingLLMMapper, EmbeddingLLMMapperConfig
    from app.mapper.fallback_mapper import EmptyFallbackMapper

    store = TaxonomyStore()
    version = "2026.01"

    if version not in store._by_version:
        store.load_version(version, [
            TaxonomyNode(
                id=1012, area="Administração", subarea="Gestão",
                conceito="Planejamento Estratégico",
                descricao="Modelos e ferramentas de planejamento estratégico",
                palavras_chave=["swot", "missão", "visão", "objetivos", "análise estratégica"],
                nivel="intermediario", critico=True
            ),
            TaxonomyNode(
                id=1001, area="Administração", subarea="Fundamentos",
                conceito="Teorias Administrativas",
                descricao="Escolas e teorias da administração",
                palavras_chave=["taylor", "fayol", "weber", "teoria", "administração científica"],
                nivel="basico", critico=False
            ),
        ])

    # Embeddings endpoint (você implementa ou aponta para seu provedor)
    # Ex.: EMBED_URL=http://localhost:9001
    import os
    embed_cfg = HttpClientConfig(
        base_url=os.getenv("EMBED_URL", "http://localhost:9001"),
        api_key=os.getenv("EMBED_API_KEY"),
        timeout_seconds=int(os.getenv("EMBED_TIMEOUT", "15")),
    )
    llm_cfg = HttpClientConfig(
        base_url=os.getenv("LLM_URL", "http://localhost:9002"),
        api_key=os.getenv("LLM_API_KEY"),
        timeout_seconds=int(os.getenv("LLM_TIMEOUT", "20")),
    )

    embed_client = SimpleHttpEmbeddingClient(embed_cfg, path="/embed")
    llm_client = SimpleHttpLLMJsonClient(llm_cfg, path="/llm/json")

    # Build taxonomy embedding index once
    nodes = store.get_nodes(version)
    index = build_index(version, nodes, embed_client)

    mapper = EmbeddingLLMMapper(
        embedder=embed_client,
        index=index,
        cfg=EmbeddingLLMMapperConfig(top_k=30, min_similarity=0.30, use_llm_refine=True),
        llm=llm_client,
    )
    fallback = EmptyFallbackMapper()

    cache = SimpleTTLCache(ttl_seconds=30 * 24 * 3600)
    audit = AuditRepository()

    _ENGINE_SINGLETON = EquivalenceEngine(store, mapper, fallback, cache, audit)
    return _ENGINE_SINGLETON

@router.post("/v1/equivalences/evaluate")
def evaluate(
    req: EvaluateRequest,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")
):
    # 1) resolve request_id
    request_id = req.request_id or idempotency_key or str(uuid.uuid4())
    req.request_id = request_id  # garante

    # 2) se já existe resultado, retorna sem recalcular
    existing = get_existing_result(db, tenant_id, request_id)
    if existing:
        return {
            "request_id": existing.request_id,
            "decisao": existing.decision,
            "score": existing.score,
            "breakdown": existing.breakdown,
            "faltantes": existing.missing,
            "criticos_faltantes": existing.missing_critical,
            "justificativa_curta": existing.justificativa_curta,
            "justificativa_detalhada": existing.justificativa_detalhada,
            "degraded_mode": existing.degraded_mode,
            "model_version": existing.model_version,
            "policy_version": existing.policy_version,
            "taxonomy_version": existing.taxonomy_version,
            "timings_ms": existing.timings_ms,
            "cached": True
        }

    # 3) processa
    engine = get_engine()
    resp = engine.evaluate(req, tenant_id)

    # 4) salvar no DB (em teoria seu engine/worker já faz, mas endpoint síncrono precisa salvar)
    # Se você já salva no engine, ótimo. Se não, faça aqui.
    return resp.model_dump() if hasattr(resp, "model_dump") else resp
