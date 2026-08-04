"""Watchdog: guards the whole peer, not a single request.

While the deadline tracker watches one outgoing request, the watchdog watches
the main loop itself. If no heartbeat arrives for longer than the configured
threshold - a crashed model, a stalled connection - it persists the state and
performs a controlled shutdown, so the match can be recovered and the log
survives instead of the process dying silently (rulebook ch. 8.4.2).

The clock and the two callbacks are injected, so the watchdog is fully testable
without sleeping and without touching the filesystem.
"""

from __future__ import annotations

import time
from collections.abc import Callable

STATUS_ALIVE = "ALIVE"
STATUS_SHUTDOWN = "SHUTDOWN"


class Watchdog:
    """Monitors heartbeats from the main loop and reacts to a freeze."""

    def __init__(
        self,
        timeout_sec: float,
        on_persist: Callable[[], None] | None = None,
        on_shutdown: Callable[[], None] | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        """Create a watchdog.

        Args:
            timeout_sec: freeze duration after which the watchdog intervenes.
            on_persist: called first, to save state for later recovery.
            on_shutdown: called second, to release connections and close logs.
            clock: monotonic time source, injected for testability.

        Raises:
            ValueError: if the timeout is not positive.
        """
        if timeout_sec <= 0:
            raise ValueError(f"timeout must be positive, got {timeout_sec}")
        self._timeout = timeout_sec
        self._on_persist = on_persist
        self._on_shutdown = on_shutdown
        self._clock = clock
        self._last_beat = clock()
        self._triggered = False

    @property
    def timeout_sec(self) -> float:
        """The freeze threshold."""
        return self._timeout

    @property
    def triggered(self) -> bool:
        """Whether the watchdog has already fired."""
        return self._triggered

    def beat(self) -> None:
        """Record a heartbeat from the main loop."""
        self._last_beat = self._clock()

    def elapsed(self) -> float:
        """Seconds since the last heartbeat."""
        return self._clock() - self._last_beat

    def check(self) -> str:
        """Test the heartbeat and intervene if the loop appears frozen.

        Returns:
            ``ALIVE`` while beats keep arriving, ``SHUTDOWN`` once the watchdog
            has persisted state and shut the peer down. Firing is idempotent:
            the callbacks run at most once.
        """
        if self._triggered:
            return STATUS_SHUTDOWN
        if self.elapsed() <= self._timeout:
            return STATUS_ALIVE
        self._triggered = True
        if self._on_persist is not None:
            self._on_persist()
        if self._on_shutdown is not None:
            self._on_shutdown()
        return STATUS_SHUTDOWN

    def reset(self) -> None:
        """Re-arm the watchdog after a recovery."""
        self._triggered = False
        self.beat()

    def __repr__(self) -> str:
        """Developer-facing summary."""
        return f"Watchdog(timeout={self._timeout}s, triggered={self._triggered})"
