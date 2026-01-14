from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.rate_limit_config import ROLE_LIMITS, PATH_LIMITS, PUBLIC_PATHS, Limit
from app.rate_limiter import check_rate_limit

def _is_public(path: str) -> bool:
    return path in PUBLIC_PATHS

def _match_limit(path: str, role: str) -> Limit:
    # 1) override por path
    for prefix, lim in PATH_LIMITS:
        if path.startswith(prefix):
            return lim
    # 2) default por role
    return ROLE_LIMITS.get(role, ROLE_LIMITS["api-client"])

def _bucket_key(tenant_id: str, role: str, path: str) -> str:
    # agrupa por prefixo para não criar uma chave por URL com ids
    # normaliza alguns endpoints muito "variáveis"
    group = path
    if path.startswith("/v1/jobs/"):
        group = "/v1/jobs/*"
    elif path.startswith("/dashboard/result/"):
        group = "/dashboard/result/*"

    return f"rl:{tenant_id}:{role}:{group}"

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if _is_public(path):
            return await call_next(request)

        # precisa do tenant/role (definidos no auth middleware)
        tenant_id = getattr(request.state, "tenant_id", None)
        role = getattr(request.state, "role", None)

        # se ainda não tiver, deixa passar e o auth vai bloquear
        if not tenant_id or not role:
            return await call_next(request)

        lim = _match_limit(path, role)
        key = _bucket_key(tenant_id, role, path)

        result = check_rate_limit(key=key, capacity=lim.capacity, refill_per_sec=lim.refill_per_sec, requested=1)

        if not result.allowed:
            headers = {
                "Retry-After": str(result.retry_after),
                "X-RateLimit-Limit": str(lim.capacity),
                "X-RateLimit-Remaining": "0",
            }
            return JSONResponse(
                {"detail": "Rate limit exceeded", "retry_after_seconds": result.retry_after},
                status_code=429,
                headers=headers
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(lim.capacity)
        response.headers["X-RateLimit-Remaining"] = str(result.tokens_left)
        return response
