"""app.config

Configuration module (placeholder).
"""
import os

class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://eq:eq@localhost:5432/equivalence")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # RQ
    RQ_QUEUE_NAME = os.getenv("RQ_QUEUE_NAME", "equivalence")

    # Cache
    EMBEDDING_CACHE_TTL = int(os.getenv("EMBEDDING_CACHE_TTL", "2592000"))  # 30 dias
    MAPPER_CACHE_TTL = int(os.getenv("MAPPER_CACHE_TTL", "2592000"))

settings = Settings()
DEBUG = True
