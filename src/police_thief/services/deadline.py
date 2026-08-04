"""Deadline tracking for outgoing requests.

Never wait unboundedly on a resource outside your control. Every request sent
over MCP carries a timestamp and an expiry; once the expiry passes, the request
is a *failure*, not an invitation to keep waiting. Leaving a request hanging is
the direct recipe for deadlock (rulebook ch. 8.4.1).

The clock is injected rather than read from the module, so tests drive time
directly and never sleep.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass


class DeadlineExpiredError(TimeoutError):
    """Raised when a tracked request outlives its expiry."""


@dataclass(frozen=True)
class Pending:
    """A request that is in flight."""

    label: str
    sent_at: float
    expires_at: float

    def remaining(self, now: float) -> float:
        """Seconds left before this request expires; negative once overdue."""
        return self.expires_at - now


class DeadlineTracker:
    """Tracks in-flight requests and reports the ones that have expired."""

    def __init__(self, timeout_sec: float, clock: Callable[[], float] = time.monotonic) -> None:
        """Create a tracker.

        Args:
            timeout_sec: how long a request may stay in flight.
            clock: monotonic time source, injected for testability.

        Raises:
            ValueError: if the timeout is not positive.
        """
        if timeout_sec <= 0:
            raise ValueError(f"timeout must be positive, got {timeout_sec}")
        self._timeout = timeout_sec
        self._clock = clock
        self._pending: dict[str, Pending] = {}

    @property
    def timeout_sec(self) -> float:
        """The expiry applied to every new request."""
        return self._timeout

    @property
    def in_flight(self) -> tuple[str, ...]:
        """Labels of the requests currently being awaited."""
        return tuple(self._pending)

    def start(self, label: str) -> Pending:
        """Register a request as in flight and stamp its expiry."""
        now = self._clock()
        pending = Pending(label=label, sent_at=now, expires_at=now + self._timeout)
        self._pending[label] = pending
        return pending

    def complete(self, label: str) -> float:
        """Mark a request as answered and return how long it took.

        Raises:
            KeyError: if the label was never started.
        """
        pending = self._pending.pop(label)
        return self._clock() - pending.sent_at

    def expired(self) -> list[Pending]:
        """Every in-flight request whose expiry has already passed."""
        now = self._clock()
        return [pending for pending in self._pending.values() if pending.remaining(now) <= 0]

    def check(self, label: str) -> None:
        """Raise if a specific request is overdue.

        Raises:
            DeadlineExpiredError: once the request's expiry has passed.
        """
        pending = self._pending.get(label)
        if pending is None:
            return
        remaining = pending.remaining(self._clock())
        if remaining <= 0:
            raise DeadlineExpiredError(
                f"request {label!r} exceeded its {self._timeout}s deadline"
            )

    def check_all(self) -> None:
        """Raise if any in-flight request is overdue.

        Raises:
            DeadlineExpiredError: naming the first overdue request found.
        """
        overdue = self.expired()
        if overdue:
            raise DeadlineExpiredError(
                f"request {overdue[0].label!r} exceeded its {self._timeout}s deadline"
            )

    def clear(self) -> None:
        """Forget every in-flight request, e.g. when abandoning a turn."""
        self._pending.clear()
