"""State rescued when the watchdog fires.

A frozen peer must not simply die: the watchdog persists whatever the match had
reached and then shuts down in a controlled way, so the log survives and the
game can be recovered. This tiny object holds that rescued state, keeping the
concern out of the orchestrator itself.
"""

from __future__ import annotations

from typing import Any


class Recovery:
    """Holds the state saved by the watchdog and whether shutdown ran."""

    def __init__(self) -> None:
        """Start with nothing rescued and no shutdown performed."""
        self.state: Any = None
        self.shutdown_called = False

    def persist(self, state: Any) -> None:
        """Save the current match state for later recovery."""
        self.state = state

    def shutdown(self) -> None:
        """Record that connections were released and logs closed."""
        self.shutdown_called = True
