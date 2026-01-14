from __future__ import annotations
from typing import Any, Dict, Optional
import time

class SimpleTTLCache:
    def __init__(self, ttl_seconds: int = 7 * 24 * 3600, max_items: int = 10000):
        self.ttl = ttl_seconds
        self.max = max_items
        self._store: Dict[str, Any] = {}
        self._exp: Dict[str, float] = {}

    def get(self, key: str) -> Optional[Any]:
        now = time.time()
        exp = self._exp.get(key)
        if exp is None or exp < now:
            self._store.pop(key, None)
            self._exp.pop(key, None)
            return None
        return self._store.get(key)

    def set(self, key: str, value: Any) -> None:
        if len(self._store) >= self.max:
            # MVP: remove arbitrário. Produção: LRU.
            k = next(iter(self._store.keys()))
            self._store.pop(k, None)
            self._exp.pop(k, None)
        self._store[key] = value
        self._exp[key] = time.time() + self.ttl
