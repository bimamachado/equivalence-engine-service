import time
import threading
from collections import defaultdict
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from app.metrics import render_prometheus

_lock = threading.Lock()

# counters
REQUESTS = defaultdict(int)      # (path, method, status)
DECISIONS = defaultdict(int)     # (tenant, decision)
DEGRADED = defaultdict(int)      # (tenant, degraded_bool)
ERRORS = defaultdict(int)        # (where, type)

# hist: latência simples em buckets
LAT_BUCKETS_MS = [50, 100, 200, 500, 1000, 2000, 5000, 10000]
LAT_HIST = defaultdict(lambda: [0] * (len(LAT_BUCKETS_MS) + 1))  # (path, method) -> counts per bucket+inf

def observe_request(path: str, method: str, status: int, latency_ms: int):
    with _lock:
        REQUESTS[(path, method, status)] += 1
        # bucketize
        idx = len(LAT_BUCKETS_MS)  # +Inf
        for i, b in enumerate(LAT_BUCKETS_MS):
            if latency_ms <= b:
                idx = i
                break
        LAT_HIST[(path, method)][idx] += 1

def observe_decision(tenant: str, decision: str, degraded: bool):
    with _lock:
        DECISIONS[(tenant, decision)] += 1
        DEGRADED[(tenant, str(degraded).lower())] += 1

def observe_error(where: str, err_type: str):
    with _lock:
        ERRORS[(where, err_type)] += 1

def render_prometheus() -> str:
    lines = []
    lines.append("# HELP http_requests_total Total HTTP requests")
    lines.append("# TYPE http_requests_total counter")
    with _lock:
        for (path, method, status), v in REQUESTS.items():
            lines.append(f'http_requests_total{{path="{path}",method="{method}",status="{status}"}} {v}')

        lines.append("# HELP http_request_latency_ms_bucket Request latency histogram buckets")
        lines.append("# TYPE http_request_latency_ms_bucket counter")
        for (path, method), buckets in LAT_HIST.items():
            cumulative = 0
            for i, b in enumerate(LAT_BUCKETS_MS):
                cumulative += buckets[i]
                lines.append(f'http_request_latency_ms_bucket{{path="{path}",method="{method}",le="{b}"}} {cumulative}')
            cumulative += buckets[-1]
            lines.append(f'http_request_latency_ms_bucket{{path="{path}",method="{method}",le="+Inf"}} {cumulative}')

        lines.append("# HELP equivalence_decisions_total Decisions by tenant")
        lines.append("# TYPE equivalence_decisions_total counter")
        for (tenant, decision), v in DECISIONS.items():
            lines.append(f'equivalence_decisions_total{{tenant="{tenant}",decision="{decision}"}} {v}')

        lines.append("# HELP equivalence_degraded_total Degraded mode occurrences")
        lines.append("# TYPE equivalence_degraded_total counter")
        for (tenant, degraded), v in DEGRADED.items():
            lines.append(f'equivalence_degraded_total{{tenant="{tenant}",degraded="{degraded}"}} {v}')

        lines.append("# HELP equivalence_errors_total Error counts")
        lines.append("# TYPE equivalence_errors_total counter")
        for (where, err_type), v in ERRORS.items():
            lines.append(f'equivalence_errors_total{{where="{where}",type="{err_type}"}} {v}')

    return "\n".join(lines) + "\n"

@router.get("/metrics", response_class=PlainTextResponse)
def metrics():
    return render_prometheus()