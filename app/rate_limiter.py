import time
import math
from dataclasses import dataclass
from app.redis_client import redis_conn

LUA_TOKEN_BUCKET = r"""
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_per_sec = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local requested = tonumber(ARGV[4])

local data = redis.call("HMGET", key, "tokens", "ts")
local tokens = tonumber(data[1])
local ts = tonumber(data[2])

if tokens == nil then
  tokens = capacity
  ts = now
end

-- refill
local delta = math.max(0, now - ts)
local refill = delta * refill_per_sec
tokens = math.min(capacity, tokens + refill)
ts = now

local allowed = 0
local retry_after = 0

if tokens >= requested then
  tokens = tokens - requested
  allowed = 1
else
  allowed = 0
  local needed = requested - tokens
  retry_after = math.ceil(needed / refill_per_sec)
end

redis.call("HMSET", key, "tokens", tokens, "ts", ts)
-- TTL: bucket expira depois de um tempo sem uso (evita lixo infinito)
redis.call("EXPIRE", key, math.ceil((capacity / refill_per_sec) * 2))

return {allowed, tokens, retry_after}
"""

_bucket_script = redis_conn.register_script(LUA_TOKEN_BUCKET)

@dataclass
class RateLimitResult:
    allowed: bool
    tokens_left: int
    retry_after: int

def _now() -> float:
    return time.time()

def check_rate_limit(key: str, capacity: int, refill_per_sec: float, requested: int = 1) -> RateLimitResult:
    now = _now()
    res = _bucket_script(
        keys=[key],
        args=[capacity, refill_per_sec, now, requested]
    )

    allowed = bool(int(res[0]))
    tokens_left = int(float(res[1]))
    retry_after = int(res[2])

    return RateLimitResult(allowed=allowed, tokens_left=tokens_left, retry_after=retry_after)
