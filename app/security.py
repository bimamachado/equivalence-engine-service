import os
import hmac
import hashlib

_API_SALT = os.getenv("API_KEY_SALT", "change-me-in-prod").encode("utf-8")

def hash_api_key(api_key: str) -> str:
    # HMAC-SHA256(api_key, SALT) -> hex
    return hmac.new(_API_SALT, api_key.encode("utf-8"), hashlib.sha256).hexdigest()

def constant_time_equals(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))
