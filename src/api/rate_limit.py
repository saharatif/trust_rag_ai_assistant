from collections import defaultdict, deque
from threading import Lock
from time import time
from typing import Callable

from fastapi import HTTPException, Request, status


class InMemoryRateLimiter:
    """Per-client sliding-window rate limiter backed by in-process memory.

    Uses a deque of timestamps per client so only requests inside the current
    window are counted — more accurate than fixed-window counters that reset
    abruptly at the end of each period.

    Thread-safe for multi-threaded ASGI workers (e.g. uvicorn with workers>1
    in the same process). NOT safe across multiple processes or containers —
    replace with Redis-backed throttling (or AWS API Gateway) when scaling
    beyond a single replica.
    """

    def __init__(self) -> None:
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def limit(self, *, requests: int, seconds: int) -> Callable[[Request], None]:
        """Return a FastAPI dependency that enforces a rate limit.

        Args:
            requests: Maximum number of requests allowed per window.
            seconds:  Length of the sliding window in seconds.
        """
        if requests <= 0:
            raise ValueError("requests must be greater than zero")
        if seconds <= 0:
            raise ValueError("seconds must be greater than zero")

        def check_rate_limit(request: Request) -> None:
            client_id = self._client_id(request)
            now = time()
            window_start = now - seconds

            with self._lock:
                timestamps = self._requests[client_id]

                # Drop timestamps that have fallen outside the current window
                while timestamps and timestamps[0] <= window_start:
                    timestamps.popleft()

                if len(timestamps) >= requests:
                    # Tell the client how many seconds to wait before retrying
                    retry_after = max(1, int(seconds - (now - timestamps[0])))
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Rate limit exceeded",
                        headers={"Retry-After": str(retry_after)},
                    )

                timestamps.append(now)

                # Prune stale client entries to prevent unbounded memory growth.
                # A client whose deque is empty has no recent activity — safe to remove.
                stale = [ip for ip, ts in self._requests.items() if not ts]
                for ip in stale:
                    del self._requests[ip]

        return check_rate_limit

    def reset(self) -> None:
        """Clear all rate limit state — intended for use between tests."""
        with self._lock:
            self._requests.clear()

    @staticmethod
    def _client_id(request: Request) -> str:
        # Prefer X-Forwarded-For so the real client IP is used when the app
        # sits behind a proxy, load balancer, or API Gateway (common in production).
        # Fall back to the direct connection IP, then to a shared sentinel.
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Header can contain a comma-separated chain of IPs; the first is the origin
            return forwarded_for.split(",")[0].strip()
        if request.client and request.client.host:
            return request.client.host
        # All requests with no identifiable client share this bucket.
        # In practice this should not happen behind a properly configured proxy.
        return "unknown"


rate_limiter = InMemoryRateLimiter()
