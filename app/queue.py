from rq import Queue
try:
    # rq >= 1.0 exposes Retry in rq.retry
    from rq.retry import Retry
except Exception:
    try:
        # older/newer layouts may expose Retry at top-level
        from rq import Retry
    except Exception:
        # Fallback minimal Retry implementation so app can run
        class Retry:
            def __init__(self, max=0, interval=None):
                self.max = max
                self.interval = interval
from app.redis_client import redis_conn
from app.config import settings

queue = Queue(name=settings.RQ_QUEUE_NAME, connection=redis_conn)
dead_queue = Queue(name=f"{settings.RQ_QUEUE_NAME}-dead", connection=redis_conn)

def default_retry():
    # backoff “bonito e funcional”: 10s, 30s, 2m, 5m, 15m
    return Retry(max=5, interval=[10, 30, 120, 300, 900])
