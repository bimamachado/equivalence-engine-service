import redis
from app.config import settings

redis_conn = redis.Redis.from_url(settings.REDIS_URL, decode_responses=False)
