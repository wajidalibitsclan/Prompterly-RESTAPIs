"""
Rate limiting configuration using slowapi.

Provides tiered rate limits:
  - strict:  5/minute   — login, password reset, OTP (brute-force protection)
  - auth:    10/minute  — registration, email change, 2FA setup
  - default: 60/minute  — general API endpoints
  - relaxed: 120/minute — read-heavy endpoints (lists, search)

Uses client IP as the key. Falls back to in-memory storage if Redis is unavailable.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.core.config import settings


def _get_client_ip(request: Request) -> str:
    """Extract real client IP, respecting X-Forwarded-For behind proxies."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return get_remote_address(request)


# Try Redis, fall back to in-memory
_storage_uri = None
try:
    import redis
    r = redis.from_url(settings.REDIS_URL, socket_connect_timeout=1)
    r.ping()
    _storage_uri = settings.REDIS_URL
except Exception:
    _storage_uri = "memory://"

limiter = Limiter(
    key_func=_get_client_ip,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"],
    storage_uri=_storage_uri,
    strategy="fixed-window",
)

# Pre-defined rate limit strings for use as decorators
STRICT = "5/minute"       # Login, password reset, OTP verification
AUTH = "10/minute"         # Registration, email change, 2FA setup
DEFAULT = f"{settings.RATE_LIMIT_PER_MINUTE}/minute"   # General endpoints
RELAXED = "120/minute"     # Read-heavy endpoints
