"""Simple in-memory rate limiting for MVP."""
import time
from collections import defaultdict
from typing import Optional

from fastapi import Header, Request

from app.core.config import settings
from app.core.errors import RateLimitError


class RateLimiter:
    """In-memory rate limiter using sliding window."""
    
    def __init__(self, max_requests: int, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # Dictionary to store request timestamps per key
        self._requests: dict[str, list[float]] = defaultdict(list)
    
    def check_rate_limit(self, key: str) -> None:
        """
        Check if request is within rate limit.
        
        Args:
            key: Identifier for rate limiting (client_id or IP)
            
        Raises:
            RateLimitError: If rate limit exceeded
        """
        now = time.time()
        cutoff = now - self.window_seconds
        
        # Remove old timestamps
        self._requests[key] = [ts for ts in self._requests[key] if ts > cutoff]
        
        # Check limit
        if len(self._requests[key]) >= self.max_requests:
            raise RateLimitError(
                f"Rate limit exceeded. Max {self.max_requests} requests per {self.window_seconds} seconds."
            )
        
        # Record this request
        self._requests[key].append(now)
    
    def cleanup_old_entries(self) -> None:
        """Periodically cleanup old entries to prevent memory growth."""
        now = time.time()
        cutoff = now - self.window_seconds
        
        for key in list(self._requests.keys()):
            self._requests[key] = [ts for ts in self._requests[key] if ts > cutoff]
            if not self._requests[key]:
                del self._requests[key]


# Global rate limiter instance
rate_limiter = RateLimiter(
    max_requests=settings.rate_limit_per_minute,
    window_seconds=60
)


async def check_rate_limit(
    request: Request,
    x_client_id: Optional[str] = Header(None)
) -> None:
    """
    Dependency to check rate limit for requests.
    Uses client_id if provided, falls back to IP address.
    """
    # Use client_id if provided, otherwise use IP
    key = x_client_id if x_client_id else request.client.host if request.client else "unknown"
    rate_limiter.check_rate_limit(key)

