"""Transport abstraction between a peer and its opponent.

The runtime talks to a :class:`Transport`, not to the network. That keeps the
protocol logic testable without a live opponent - guidelines rule 7 forbids
tests that depend on external services - and it means a tunnel URL, a localhost
port and an in-process loopback are interchangeable.

The interface is deliberately synchronous: the turn loop is sequential by
nature, and the async MCP client is wrapped where it is actually used.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


class TransportError(RuntimeError):
    """Raised when a message cannot be delivered to the opponent."""


@runtime_checkable
class Transport(Protocol):
    """Anything able to deliver a message to the opponent and return its reply."""

    def send(self, tool: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Deliver ``payload`` to the opponent's ``tool`` and return the reply."""
        ...  # pragma: no cover - protocol declaration


class LoopbackTransport:
    """Delivers messages straight into a local handler, with no network.

    Used for development and for tests: two peers can play a complete match in
    one process while still exchanging exactly the messages they would send over
    a tunnel. It is *not* how a league match runs - the two sides must be
    separate processes there - but the message flow is identical.
    """

    def __init__(self, handler: Any) -> None:
        """Wrap an object exposing one method per tool name."""
        self._handler = handler
        self._sent: list[tuple[str, dict[str, Any]]] = []

    @property
    def sent(self) -> tuple[tuple[str, dict[str, Any]], ...]:
        """Every message delivered so far, for assertions and diagnostics."""
        return tuple(self._sent)

    def send(self, tool: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Route a message to the handler method named ``tool``.

        Raises:
            TransportError: if the handler exposes no such tool.
        """
        method = getattr(self._handler, tool, None)
        if not callable(method):
            raise TransportError(f"opponent exposes no tool named {tool!r}")
        self._sent.append((tool, payload))
        return method(payload)


class FlakyTransport:
    """Wraps a transport and fails the first ``failures`` deliveries.

    Exists so retry and technical-loss paths can be exercised deterministically
    instead of hoping a real network misbehaves at the right moment.
    """

    def __init__(self, inner: Transport, failures: int) -> None:
        """Wrap ``inner``, failing the next ``failures`` calls."""
        self._inner = inner
        self._remaining = failures

    def send(self, tool: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Fail while the failure budget lasts, then delegate."""
        if self._remaining > 0:
            self._remaining -= 1
            raise TransportError(f"simulated delivery failure for {tool!r}")
        return self._inner.send(tool, payload)
