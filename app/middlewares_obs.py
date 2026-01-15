import time
from urllib import request
import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.metrics import observe_request

logger = logging.getLogger("equivalence")

class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()

        # correlation id: usa Idempotency-Key se tiver, senão gera
        rid = request.headers.get("Idempotency-Key") or str(uuid.uuid4())
        request.state.request_id = rid

        response = None
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        finally:
            latency_ms = int((time.time() - start) * 1000)

            tenant_id = getattr(request.state, "tenant_id", None)
            role = getattr(request.state, "role", None)

            logger.info(
                "access",
                extra={
                    "event": "access",
                    "request_id": rid,
                    "tenant_id": tenant_id,
                    "role": role,
                    "path": request.url.path,
                    "method": request.method,
                    "status_code": status,
                    "latency_ms": latency_ms,
                },
            )
            observe_request(request.url.path, request.method, status, latency_ms)
            if response is not None:
                response.headers["X-Request-Id"] = rid
                response.headers["X-Response-Time-ms"] = str(latency_ms)
