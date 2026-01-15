from __future__ import annotations
from fastapi import FastAPI
from app.bootstrap import init_db

from app.middlewares import ApiKeyAuthMiddleware
from app.middlewares_rate import RateLimitMiddleware
from app.middlewares_obs import ObservabilityMiddleware
from app.logging_setup import setup_logging

from app.api.routes import router as eval_router
from app.api.batch_routes import router as batch_router
from app.dashboard import router as dash_router
from app.admin_routes import router as admin_router
from app.admin_dlq_routes import router as dlq_router
from app.metrics_routes import router as metrics_router
from app.readiness import router as readiness_router

router = APIRouter()

def get_engine() -> EquivalenceEngine:
    # Aqui você injeta dependências reais via container.
    from app.taxonomy.store import TaxonomyStore
    from app.taxonomy.models import TaxonomyNode
    from app.mapper.stub_mapper import StubKeywordMapper
    from app.mapper.fallback_mapper import EmptyFallbackMapper
    from app.cache.cache import SimpleTTLCache
    from app.audit.repository import AuditRepository

    store = TaxonomyStore()

    # Carrega uma taxonomia MVP só pra não ficar vazio.
    # Produção: carregar do DB por tenant/version.
    if "2026.01" not in store._by_version:
        store.load_version("2026.01", [
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

    mapper = StubKeywordMapper(store)
    fallback = EmptyFallbackMapper()
    cache = SimpleTTLCache(ttl_seconds=30*24*3600)
    audit = AuditRepository()
    return EquivalenceEngine(store, mapper, fallback, cache, audit)

@router.post("/v1/equivalences/evaluate", response_model=EvaluateResponse)
def evaluate(req: EvaluateRequest, engine: EquivalenceEngine = Depends(get_engine)) -> EvaluateResponse:
    return engine.evaluate(req)
app = FastAPI(title="Equivalence Engine Service", version="1.0.0")

@app.on_event("startup")
def _startup():
    setup_logging()


# Ordem: RateLimit primeiro, Auth depois (Auth roda primeiro)
app.add_middleware(ObservabilityMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(ApiKeyAuthMiddleware)


app.include_router(eval_router)
app.include_router(batch_router)
app.include_router(dash_router)
app.include_router(admin_router)
app.include_router(dlq_router)
app.include_router(metrics_router)
app.add_middleware(ObservabilityMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(ApiKeyAuthMiddleware)
app.include_router(readiness_router)

@app.get("/health")
def health():
    return {"status": "alive"}