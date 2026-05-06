from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.rate_limit import InMemoryRateLimiter, rate_limiter


# --- Helper ---

def make_request(host: str = "127.0.0.1", forwarded_for: str | None = None):
    """Build a minimal fake Request object for unit testing the limiter."""
    headers = {}
    if forwarded_for:
        headers["x-forwarded-for"] = forwarded_for
    return SimpleNamespace(
        client=SimpleNamespace(host=host),
        headers=headers,
    )


# --- Unit tests ---

def test_rate_limiter_allows_requests_under_limit():
    limiter = InMemoryRateLimiter()
    check = limiter.limit(requests=2, seconds=60)

    check(make_request())
    check(make_request())  # second request should still be allowed


def test_rate_limiter_rejects_requests_over_limit():
    limiter = InMemoryRateLimiter()
    check = limiter.limit(requests=1, seconds=60)

    check(make_request())
    with pytest.raises(HTTPException) as exc_info:
        check(make_request())

    assert exc_info.value.status_code == 429
    assert exc_info.value.detail == "Rate limit exceeded"
    assert "Retry-After" in exc_info.value.headers


def test_rate_limiter_tracks_clients_independently():
    # Requests from different IPs must not share a bucket
    limiter = InMemoryRateLimiter()
    check = limiter.limit(requests=1, seconds=60)

    check(make_request(host="1.1.1.1"))
    check(make_request(host="2.2.2.2"))  # different client — should be allowed


def test_rate_limiter_uses_x_forwarded_for_over_direct_ip():
    # When behind a proxy the real client IP is in X-Forwarded-For.
    # Two requests with the same forwarded IP must share a bucket even if
    # the direct connection IP differs.
    limiter = InMemoryRateLimiter()
    check = limiter.limit(requests=1, seconds=60)

    check(make_request(host="proxy-ip", forwarded_for="real-client-ip"))
    with pytest.raises(HTTPException) as exc_info:
        check(make_request(host="proxy-ip", forwarded_for="real-client-ip"))

    assert exc_info.value.status_code == 429


def test_rate_limiter_uses_first_ip_in_forwarded_for_chain():
    # X-Forwarded-For can be a comma-separated chain; the first entry is the origin
    limiter = InMemoryRateLimiter()
    check = limiter.limit(requests=1, seconds=60)

    check(make_request(forwarded_for="origin-ip, proxy1, proxy2"))
    with pytest.raises(HTTPException):
        check(make_request(forwarded_for="origin-ip, proxy1, proxy2"))


def test_rate_limiter_handles_no_client():
    # When request.client is None (can happen in some proxy/test setups),
    # the limiter falls back to "unknown" and should not crash
    limiter = InMemoryRateLimiter()
    check = limiter.limit(requests=2, seconds=60)
    request = SimpleNamespace(client=None, headers={})

    check(request)  # should not raise


def test_reset_clears_all_state():
    limiter = InMemoryRateLimiter()
    check = limiter.limit(requests=1, seconds=60)

    check(make_request())  # exhaust the limit
    limiter.reset()
    check(make_request())  # should be allowed again after reset


def test_invalid_limit_config_raises():
    limiter = InMemoryRateLimiter()
    with pytest.raises(ValueError):
        limiter.limit(requests=0, seconds=60)
    with pytest.raises(ValueError):
        limiter.limit(requests=1, seconds=0)


# --- Integration tests (full HTTP stack) ---

client = TestClient(app)


def test_health_is_not_rate_limited():
    # /health must never be rate-limited — load balancers call it continuously
    rate_limiter.reset()
    for _ in range(200):
        response = client.get("/health")
        assert response.status_code == 200


def test_ingest_returns_429_when_rate_limit_exceeded():
    rate_limiter.reset()

    valid_payload = {
        "documents": [
            {
                "id": "doc_001",
                "title": "Travel Policy",
                "source_type": "policy",
                "department": "HR",
                "text": "Employees must submit receipts within 30 days.",
            }
        ]
    }

    from src.utils.config import get_settings
    limit = get_settings().ingest_rate_limit_per_minute

    # Exhaust the limit
    for _ in range(limit):
        client.post("/ingest", json=valid_payload)

    # Next request must be rejected
    response = client.post("/ingest", json=valid_payload)
    assert response.status_code == 429
    assert response.json()["detail"] == "Rate limit exceeded"
    assert "Retry-After" in response.headers

    rate_limiter.reset()
