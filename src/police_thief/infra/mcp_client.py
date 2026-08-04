"""Outbound side of a peer: every call it makes to its opponent.

Each call is wrapped in a deadline (a request that outlives its expiry is a
failure, not patience) and in a bounded retry with backoff. When the retries are
exhausted the caller is told plainly, so the runtime can take the emergency exit
to a technical loss instead of hanging - which is exactly the deadlock the
rulebook's reliability chapter is about.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from ..domain import messages
from ..services.deadline import DeadlineTracker
from ..shared.schema import NetworkConfig, RateLimiterConfig
from .transport import Transport, TransportError


class PeerUnreachableError(RuntimeError):
    """Raised when the opponent could not be reached within the retry budget."""


class PeerClient:
    """Sends protocol messages to the opponent and returns its replies."""

    def __init__(
        self,
        transport: Transport,
        network: NetworkConfig,
        limits: RateLimiterConfig,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        """Bind the client to a transport and the contract's timing rules."""
        self._transport = transport
        self._limits = limits
        self._sleep = sleep
        self._deadlines = DeadlineTracker(network.response_timeout_sec, clock=clock)

    @property
    def deadlines(self) -> DeadlineTracker:
        """The tracker stamping an expiry on every outgoing request."""
        return self._deadlines

    def call(self, tool: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Send one message, retrying transient failures within the budget.

        Returns:
            The opponent's reply.

        Raises:
            PeerUnreachableError: once every attempt has failed. The caller must
                treat this as a failure and close the turn, never as a reason to
                keep waiting.
            DeadlineExpiredError: if a reply arrives after the expiry.
        """
        attempts = self._limits.max_retries
        last_error: Exception | None = None
        for attempt in range(1, attempts + 1):
            label = f"{tool}#{attempt}"
            self._deadlines.start(label)
            try:
                reply = self._transport.send(tool, payload)
            except TransportError as error:
                last_error = error
                self._deadlines.clear()
                if attempt < attempts:
                    self._sleep(self._limits.retry_backoff_sec)
                continue
            self._deadlines.check(label)
            self._deadlines.complete(label)
            return reply
        raise PeerUnreachableError(
            f"{tool}: opponent unreachable after {attempts} attempts ({last_error})"
        )

    def handshake(self, role: str, config_sha256: str, games_played: int, peer_id: str) -> dict:
        """Open the match: exchange contract digest and declared game count."""
        return self.call("handshake", messages.handshake(role, config_sha256, games_played, peer_id))

    def commit(self, role: str, step: int, digest: str) -> dict[str, Any]:
        """Send this step's sealed commitment - the digest only."""
        return self.call("commit", messages.commit(role, step, digest))

    def acknowledge(self, role: str, step: int, digest: str) -> dict[str, Any]:
        """Confirm the opponent's commitment is received and locked."""
        return self.call("ack", messages.ack(role, step, digest))

    def reveal(self, role: str, step: int, move: str, intent: str, hint: str) -> dict[str, Any]:
        """Reveal the move and the verbal hint; the nonce stays secret."""
        return self.call("reveal", messages.reveal(role, step, move, intent, hint))

    def capture_claim(self, role: str, step: int, claimed: bool) -> dict[str, Any]:
        """Declare a capture, or answer a declaration truthfully."""
        return self.call("capture_claim", messages.capture_claim(role, step, claimed))

    def audit(self, role: str, entries: list[dict[str, Any]]) -> dict[str, Any]:
        """Hand over the full log, nonces included, for the mutual audit."""
        return self.call("audit", messages.audit(role, entries))
