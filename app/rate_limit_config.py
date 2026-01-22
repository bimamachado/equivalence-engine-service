from dataclasses import dataclass

@dataclass(frozen=True)
class Limit:
    capacity: int          # tokens máximos
    refill_per_sec: float  # tokens por segundo

# Defaults por role (por tenant)
ROLE_LIMITS = {
    "api-client": Limit(capacity=120, refill_per_sec=120/60),  # 120 req/min
    "auditor":    Limit(capacity=60,  refill_per_sec=60/60),   # 60 req/min
    "admin":      Limit(capacity=30,  refill_per_sec=30/60),   # 30 req/min
}

# Overrides por rota (mais caro = menos)
# match por prefixo de path
PATH_LIMITS = [
    ("/v1/equivalences/evaluate", Limit(capacity=60, refill_per_sec=60/60)),   # 60/min
    ("/v1/equivalences/batch",    Limit(capacity=10, refill_per_sec=10/60)),   # 10/min
    ("/v1/jobs",                  Limit(capacity=120, refill_per_sec=120/60)),# 120/min
    ("/dashboard",                Limit(capacity=30, refill_per_sec=30/60)),  # 30/min
    ("/admin",                    Limit(capacity=10, refill_per_sec=10/60)),  # 10/min
]

PUBLIC_PATHS = {
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/doc",
}
