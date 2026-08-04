"""Inbound side of a peer: what it does with a message from the opponent.

The handler is deliberately free of I/O and of transport details, so the same
object serves the live FastMCP server, the in-process loopback used in tests,
and the replay tooling. It validates every incoming message before acting on it:
in a zero-trust game, a peer must never accept a claim it has not checked.
"""

from __future__ import annotations

from typing import Any

from ..domain import messages
from ..domain.messages import MessageError


class HandshakeRejectedError(RuntimeError):
    """Raised when the opponent's contract does not match ours byte for byte."""


class InboundHandler:
    """Receives, validates and records the opponent's messages."""

    def __init__(self, config_sha256: str, expect_role: str) -> None:
        """Bind the handler to our contract digest and the opponent's role."""
        self._config_sha256 = config_sha256
        self._expect_role = expect_role
        self.received: list[dict[str, Any]] = []
        self.commitments: dict[int, str] = {}
        self.reveals: dict[int, dict[str, Any]] = {}
        self.opponent_games_played: int | None = None
        self.opponent_peer_id: str | None = None
        self.audit_entries: list[dict[str, Any]] = []

    def _accept(self, payload: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        """Validate an envelope and confirm it came from the expected role."""
        kind, message = messages.parse(payload)
        if message["role"] != self._expect_role:
            raise MessageError(
                f"{kind}: expected a message from {self._expect_role!r}, "
                f"got {message['role']!r}"
            )
        self.received.append(message)
        return kind, message

    def handshake(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Accept the opening message, refusing to play on a contract mismatch.

        Both peers must load a byte-for-byte identical contract; different
        digests mean different physics, so the match must not start.
        """
        _, message = self._accept(payload)
        their_digest = message.get("config_sha256")
        if their_digest != self._config_sha256:
            raise HandshakeRejectedError(
                f"contract mismatch: ours {self._config_sha256[:12]}, "
                f"theirs {str(their_digest)[:12]}"
            )
        self.opponent_games_played = message.get("games_played")
        self.opponent_peer_id = message.get("peer_id")
        return {"accepted": True, "config_sha256": self._config_sha256}

    def commit(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Record the opponent's sealed commitment for this step.

        A second commitment for the same step is refused: once sealed, a move
        cannot be replaced.
        """
        _, message = self._accept(payload)
        step = int(message["step"])
        if step in self.commitments:
            raise MessageError(f"commit: step {step} was already committed")
        self.commitments[step] = str(message["digest"])
        return {"accepted": True, "step": step}

    def ack(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Record the opponent's acknowledgement of our commitment."""
        _, message = self._accept(payload)
        return {"accepted": True, "step": message["step"]}

    def reveal(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Record a revealed move and hint, which must follow a commitment."""
        _, message = self._accept(payload)
        step = int(message["step"])
        if step not in self.commitments:
            raise MessageError(f"reveal: step {step} was never committed")
        self.reveals[step] = message
        return {"accepted": True, "step": step, "digest": self.commitments[step]}

    def capture_claim(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Record a capture claim; the truthful answer is sealed in the commit."""
        _, message = self._accept(payload)
        return {"accepted": True, "claimed": bool(message["claimed"])}

    def audit(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Receive the opponent's full log for the end-of-game mutual audit."""
        _, message = self._accept(payload)
        entries = message.get("entries") or []
        if not isinstance(entries, list):
            raise MessageError("audit: entries must be a list")
        self.audit_entries = entries
        return {"accepted": True, "entries": len(entries)}

    def committed_digest(self, step: int) -> str | None:
        """The digest the opponent sealed for ``step``, if any."""
        return self.commitments.get(step)
