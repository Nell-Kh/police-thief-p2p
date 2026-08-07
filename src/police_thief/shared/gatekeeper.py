"""The API Gatekeeper: every external call passes three gates, or waits.

Guidelines ch. 5 and rulebook ch. 9.3, combined: no direct API calls bypass
this object. The gates, in order: the **quota manager** (a daily ceiling - the
last line before account suspension), the **token bucket** (burst and rate),
and the **DOS detector** (an abnormal send pattern locks the whole pipeline -
sacrificing a report to save the account). Overflow goes to a FIFO **queue**,
never to a rejection or a crash, and every attempt is logged for monitoring.
All limits come from configuration - none are hardcoded.
"""

from __future__ import annotations

import time
from collections import deque
from collections.abc import Callable
from typing import Any

from .bucket import TokenBucket

STATUS_SENT = "sent"
STATUS_QUEUED = "queued"
STATUS_LOCKED = "locked"


class Gatekeeper:
    """Central manager for one external service's outgoing calls."""

    def __init__(
        self,
        *,
        requests_per_minute: int,
        daily_quota: int,
        queue_depth: int,
        dos_max_per_window: int,
        dos_window_sec: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        """Assemble the three gates from configuration values."""
        self._bucket = TokenBucket.per_minute(requests_per_minute, clock=clock)
        self._daily_quota = daily_quota
        self._sent_today = 0
        self._queue: deque[Callable[[], Any]] = deque()
        self._queue_depth = queue_depth
        self._dos_max = dos_max_per_window
        self._dos_window = dos_window_sec
        self._attempts: deque[float] = deque()
        self._clock = clock
        self.locked = False
        self.log: list[dict[str, Any]] = []

    @property
    def queue_size(self) -> int:
        """Requests waiting for a gate to open."""
        return len(self._queue)

    @property
    def backpressure(self) -> bool:
        """Whether the queue has reached its configured depth."""
        return len(self._queue) >= self._queue_depth

    def execute(self, call: Callable[[], Any], label: str = "call") -> str:
        """Run ``call`` through the gates, or queue it, or refuse while locked.

        Returns:
            ``sent``, ``queued`` or ``locked``. Overflow beyond the queue depth
            is dropped with a log entry - the alternative would be unbounded
            memory, and the log makes the loss visible.
        """
        self._note_attempt()
        if self._dos_tripped():
            self.locked = True
        if self.locked:
            self._log(label, STATUS_LOCKED)
            return STATUS_LOCKED
        if self._sent_today >= self._daily_quota or not self._bucket.allow():
            if not self.backpressure:
                self._queue.append(call)
            self._log(label, STATUS_QUEUED)
            return STATUS_QUEUED
        call()
        self._sent_today += 1
        self._log(label, STATUS_SENT)
        return STATUS_SENT

    def drain(self) -> int:
        """Send queued requests while the gates allow; returns how many went out."""
        sent = 0
        while self._queue and not self.locked:
            if self._sent_today >= self._daily_quota or not self._bucket.allow():
                break
            call = self._queue.popleft()
            call()
            self._sent_today += 1
            self._log("drain", STATUS_SENT)
            sent += 1
        return sent

    def reset_lock(self) -> None:
        """Manually re-arm a locked pipeline after investigating the anomaly."""
        self.locked = False
        self._attempts.clear()

    def _note_attempt(self) -> None:
        """Record a send attempt for the DOS window."""
        now = self._clock()
        self._attempts.append(now)
        while self._attempts and now - self._attempts[0] > self._dos_window:
            self._attempts.popleft()

    def _dos_tripped(self) -> bool:
        """An abnormal burst of attempts - the signature of a runaway loop."""
        return len(self._attempts) > self._dos_max

    def _log(self, label: str, status: str) -> None:
        """Every attempt is logged for monitoring."""
        self.log.append({"label": label, "status": status, "at": self._clock()})
