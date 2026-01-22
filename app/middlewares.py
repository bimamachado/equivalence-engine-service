from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.db import SessionLocal
from app.auth import get_api_key_record

PUBLIC_PATHS = {
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/metrics",
    "/test-ui",
    "/doc",
}

def _is_public(path: str) -> bool:
    return path in PUBLIC_PATHS

class ApiKeyAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if _is_public(path):
            return await call_next(request)

        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return JSONResponse({"detail": "Missing X-API-Key"}, status_code=401)

        db = SessionLocal()
        try:
            rec = get_api_key_record(db, api_key)
            if not rec:
                return JSONResponse({"detail": "Invalid API key"}, status_code=401)

            request.state.tenant_id = rec.tenant_id
            request.state.api_key_id = rec.id
            request.state.role = rec.role

            return await call_next(request)
        finally:
            db.close()
