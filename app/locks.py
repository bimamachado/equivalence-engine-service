import time
from app.redis_client import redis_conn

def acquire_lock(key: str, ttl_seconds: int = 120) -> bool:
    # NX = só cria se não existe
    # EX = expira para não virar lock eterno
    return bool(redis_conn.set(key, b"1", nx=True, ex=ttl_seconds))

def release_lock(key: str):
    try:
        redis_conn.delete(key)
    except Exception:
        pass

def lock_key(tenant_id: str, request_id: str) -> str:
    return f"lock:equiv:{tenant_id}:{request_id}"
