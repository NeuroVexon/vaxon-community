"""
Axon by NeuroVexon - Rate Limiter Tests

Tests for the in-memory RateLimiter used for MCP and API protection.
"""

from datetime import datetime, timedelta

from core.security import RateLimiter


class TestRateLimiter:
    """Tests for RateLimiter"""

    def test_allows_first_request(self):
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        assert limiter.is_allowed("user-1") is True

    def test_allows_up_to_limit(self):
        limiter = RateLimiter(max_requests=3, window_seconds=60)

        assert limiter.is_allowed("user-1") is True
        assert limiter.is_allowed("user-1") is True
        assert limiter.is_allowed("user-1") is True

    def test_blocks_over_limit(self):
        limiter = RateLimiter(max_requests=2, window_seconds=60)

        limiter.is_allowed("user-1")
        limiter.is_allowed("user-1")
        assert limiter.is_allowed("user-1") is False

    def test_different_keys_independent(self):
        limiter = RateLimiter(max_requests=1, window_seconds=60)

        assert limiter.is_allowed("user-1") is True
        assert limiter.is_allowed("user-2") is True
        assert limiter.is_allowed("user-1") is False
        assert limiter.is_allowed("user-2") is False

    def test_reset_clears_limit(self):
        limiter = RateLimiter(max_requests=1, window_seconds=60)

        limiter.is_allowed("user-1")
        assert limiter.is_allowed("user-1") is False

        limiter.reset("user-1")
        assert limiter.is_allowed("user-1") is True

    def test_reset_nonexistent_key(self):
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        limiter.reset("nonexistent")  # Should not raise

    def test_window_expiry(self):
        """Requests outside the window should not count"""
        limiter = RateLimiter(max_requests=1, window_seconds=60)

        # Manually inject an old request
        old_time = datetime.utcnow() - timedelta(seconds=120)
        limiter._requests["user-1"] = [old_time]

        # Should be allowed because old request is outside window
        assert limiter.is_allowed("user-1") is True
