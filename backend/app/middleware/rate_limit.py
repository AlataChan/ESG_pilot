"""
Rate Limiting Middleware
Prevents API abuse with configurable rate limits per endpoint
"""

import time
import logging
from typing import Callable, Optional, Dict
from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter
    Allows burst traffic while maintaining average rate
    """

    def __init__(self, rate: int, per: int):
        """
        Initialize rate limiter

        Args:
            rate: Number of requests allowed
            per: Time period in seconds
        """
        self.rate = rate
        self.per = per
        self.allowance = rate
        self.last_check = time.time()

    def is_allowed(self) -> bool:
        """Check if request is allowed"""
        current = time.time()
        time_passed = current - self.last_check
        self.last_check = current

        # Add tokens based on time passed
        self.allowance += time_passed * (self.rate / self.per)

        # Cap at rate limit
        if self.allowance > self.rate:
            self.allowance = self.rate

        # Check if we have tokens
        if self.allowance < 1.0:
            return False
        else:
            self.allowance -= 1.0
            return True

    def get_retry_after(self) -> int:
        """Get seconds until next request allowed"""
        if self.allowance >= 1.0:
            return 0
        tokens_needed = 1.0 - self.allowance
        return int(tokens_needed * (self.per / self.rate)) + 1


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware with per-IP and per-user limits

    Configuration:
    - Default: 100 requests per minute per IP
    - Authenticated users: 1000 requests per minute
    - Expensive endpoints: Custom limits
    """

    def __init__(
        self,
        app: ASGIApp,
        default_limit: int = 100,
        default_period: int = 60,
        authenticated_limit: int = 1000,
        endpoint_limits: Optional[Dict[str, tuple]] = None
    ):
        super().__init__(app)
        self.default_limit = default_limit
        self.default_period = default_period
        self.authenticated_limit = authenticated_limit
        self.endpoint_limits = endpoint_limits or {}

        # Store limiters per client
        self.limiters: Dict[str, RateLimiter] = defaultdict(
            lambda: RateLimiter(self.default_limit, self.default_period)
        )

        # Cleanup old limiters periodically
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes

    def _get_client_key(self, request: Request) -> str:
        """Get unique identifier for client"""
        # Try to get authenticated user ID
        if hasattr(request.state, 'user') and request.state.user:
            return f"user:{request.state.user.get('id', 'unknown')}"

        # Fall back to IP address
        if request.client:
            return f"ip:{request.client.host}"

        return "unknown"

    def _get_rate_limit(self, request: Request, client_key: str) -> tuple:
        """Get rate limit for this request"""
        # Check if authenticated user
        if client_key.startswith("user:"):
            return (self.authenticated_limit, self.default_period)

        # Check for endpoint-specific limits
        path = request.url.path
        for endpoint_pattern, (limit, period) in self.endpoint_limits.items():
            if endpoint_pattern in path:
                return (limit, period)

        # Default limit
        return (self.default_limit, self.default_period)

    def _cleanup_old_limiters(self):
        """Remove inactive limiters to prevent memory leak"""
        current = time.time()
        if current - self.last_cleanup > self.cleanup_interval:
            # Remove limiters not used in last hour
            cutoff = current - 3600
            to_remove = [
                key for key, limiter in self.limiters.items()
                if limiter.last_check < cutoff
            ]
            for key in to_remove:
                del self.limiters[key]

            self.last_cleanup = current
            if to_remove:
                logger.debug(f"Cleaned up {len(to_remove)} inactive rate limiters")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting"""
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/", "/api/v1/monitoring/health"]:
            return await call_next(request)

        # Get client identifier
        client_key = self._get_client_key(request)

        # Get or create limiter for this client
        limiter_key = f"{client_key}:{request.url.path}"

        if limiter_key not in self.limiters:
            limit, period = self._get_rate_limit(request, client_key)
            self.limiters[limiter_key] = RateLimiter(limit, period)

        limiter = self.limiters[limiter_key]

        # Check if request is allowed
        if not limiter.is_allowed():
            retry_after = limiter.get_retry_after()
            logger.warning(
                f"Rate limit exceeded for {client_key} on {request.url.path}. "
                f"Retry after {retry_after}s"
            )

            response = Response(
                content='{"detail":"Rate limit exceeded. Please try again later."}',
                status_code=429,
                media_type="application/json"
            )
            response.headers["Retry-After"] = str(retry_after)
            response.headers["X-RateLimit-Limit"] = str(limiter.rate)
            response.headers["X-RateLimit-Remaining"] = "0"
            response.headers["X-RateLimit-Reset"] = str(int(time.time() + retry_after))
            return response

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(limiter.rate)
        response.headers["X-RateLimit-Remaining"] = str(int(limiter.allowance))
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + limiter.per))

        # Periodic cleanup
        self._cleanup_old_limiters()

        return response


# Predefined endpoint-specific limits
ENDPOINT_LIMITS = {
    "/api/v1/rag/answer": (20, 60),  # 20 req/min for expensive LLM calls
    "/api/v1/extraction/extract": (30, 60),  # 30 req/min for extraction
    "/api/v1/auth/login": (5, 60),  # 5 login attempts per minute
    "/api/v1/auth/register": (3, 300),  # 3 registrations per 5 minutes
}
