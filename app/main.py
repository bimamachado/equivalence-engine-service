from __future__ import annotations
from fastapi import FastAPI
from pathlib import Path
from fastapi.staticfiles import StaticFiles
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
from app.metrics import router as metrics_router
from app.readiness import router as readiness_router
from app.ui_routes import router as ui_router
app = FastAPI(title="Equivalence Engine Service", version="1.0.0")

# Mount DOCS directory at /docs so doc files are served by the app
docs_path = Path(__file__).resolve().parents[1] / "DOCS"
if docs_path.exists():
    app.mount("/docs", StaticFiles(directory=str(docs_path), html=True), name="docs")

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
app.include_router(ui_router)
app.add_middleware(ObservabilityMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(ApiKeyAuthMiddleware)
app.include_router(readiness_router)

@app.get("/health")
def health():
    return {"status": "alive"}
