"""The token-bucket rate limiter - the middle gate of the Gatekeeper.

These are *rate* tokens, not language-model tokens: load-regulation units.
The rulebook's update rule, verbatim (ch. 9.3.2):

    tokens <- min(C, tokens + r * dt),   allow <=> tokens >= 1

``C`` bounds the burst a quiet period can earn; ``r`` bounds the long-run
average rate and must stay below the provider's quota. The clock is injected
so tests drive time by hand.
"""

from __future__ import annotations

import time
from collections.abc import Callable


class TokenBucket:
    """Continuous-refill token bucket for outgoing API requests."""

    def __init__(
        self,
        capacity: float,
        refill_per_sec: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        """Create a bucket that starts full.

        Args:
            capacity: maximum tokens held - the permitted burst size.
            refill_per_sec: tokens added per second - the average rate.
            clock: monotonic time source, injected for testability.

        Raises:
            ValueError: if capacity or refill rate is not positive.
        """
        if capacity <= 0 or refill_per_sec <= 0:
            raise ValueError("capacity and refill rate must be positive")
        self.capacity = float(capacity)
        self.refill_per_sec = float(refill_per_sec)
        self._clock = clock
        self._tokens = float(capacity)
        self._last = clock()

    @property
    def tokens(self) -> float:
        """Whole-token view of the current level, refilled to now."""
        self._refill()
        return self._tokens

    def _refill(self) -> None:
        """Apply the continuous refill, clamped to capacity."""
        now = self._clock()
        elapsed = now - self._last
        self._tokens = min(self.capacity, self._tokens + elapsed * self.refill_per_sec)
        self._last = now

    def allow(self, cost: float = 1.0) -> bool:
        """Spend ``cost`` tokens if available; otherwise refuse.

        A refusal is not an error - the caller queues the request and drains
        it later, once continuous refill has accumulated a whole token.
        """
        self._refill()
        if self._tokens >= cost:
            self._tokens -= cost
            return True
        return False

    @classmethod
    def per_minute(
        cls, requests_per_minute: int, clock: Callable[[], float] = time.monotonic
    ) -> TokenBucket:
        """A bucket enforcing the contract's requests-per-minute limit."""
        return cls(
            capacity=float(requests_per_minute),
            refill_per_sec=requests_per_minute / 60.0,
            clock=clock,
        )
