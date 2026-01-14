from __future__ import annotations
import hashlib
import time
from contextlib import contextmanager

def sha256_text(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(p.encode("utf-8", errors="ignore"))
    return h.hexdigest()

@contextmanager
def timer_ms():
    start = time.time()
    yield lambda: int(round((time.time() - start) * 1000))
