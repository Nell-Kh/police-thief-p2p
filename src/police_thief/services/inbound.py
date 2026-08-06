"""Inbound side of a peer: the three tools an opponent may call.

The wire follows ADR-7 and the reference implementation: ``negotiate`` opens a
match by exchanging locked terms, ``receive_turn`` delivers one turn message
(commit hash, hint, scent - never a cleartext position), and ``submit_audit``
hands over the full disclosure at game end. Everything is validated before it
is stored: in a zero-trust game, a peer never acts on a message it has not
checked.
"""

from __future__ import annotations

from typing import Any

from ..domain.negotiation import TermsRejectedError, validate_terms
from ..domain.turnmsg import TurnMessage


class HandshakeRejectedError(RuntimeError):
    """Raised when the opponent's terms do not match ours."""


class InboundHandler:
    """Receives, validates and queues the opponent's calls."""

    def __init__(
        self, our_terms: dict[str, Any], our_extras: dict[str, Any], expect_role: str
    ) -> None:
        """Bind the handler to our signed terms, declarations and the rival role."""
        self._our_terms = our_terms
        self._our_extras = our_extras
        self._expect_role = expect_role
        self.opponent_terms: dict[str, Any] | None = None
        self.turns: list[TurnMessage] = []
        self.commitments: dict[int, str] = {}
        self.audit: dict[str, Any] | None = None

    @property
    def expect_role(self) -> str:
        """The only role whose messages this peer accepts."""
        return self._expect_role

    @property
    def opponent_games_played(self) -> int | None:
        """The opponent's declared counted-game total, once negotiated.

        None both before negotiation and when the peer declared nothing -
        per the kit, an omitted declaration is silence, never a refusal.
        """
        if self.opponent_terms is None:
            return None
        declared = self.opponent_terms.get("counted_games_played")
        return int(declared) if isinstance(declared, int) else None

    def negotiate(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Accept the opponent's terms, refusing any lock mismatch.

        Raises:
            HandshakeRejectedError: on a contract, scent-model or role
                mismatch - different physics means the race must not start.
        """
        try:
            terms = validate_terms(
                payload,
                our_terms=self._our_terms,
                our_extras=self._our_extras,
                expect_role=self._expect_role,
            )
        except TermsRejectedError as error:
            raise HandshakeRejectedError(str(error)) from error
        self.opponent_terms = terms
        return {"accepted": True, "terms": self._our_terms, **self._our_extras}

    def receive_turn(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Accept one turn message; receiving it makes it our turn.

        A second commitment for the same step is refused - once sealed, a move
        cannot be replaced.
        """
        message = TurnMessage.from_wire(payload)
        if message.sender != self._expect_role:
            raise HandshakeRejectedError(
                f"expected a turn from {self._expect_role!r}, got {message.sender!r}"
            )
        if message.step in self.commitments:
            raise HandshakeRejectedError(f"step {message.step} was already committed")
        self.commitments[message.step] = message.commit
        self.turns.append(message)
        return {"ok": True, "step": message.step}

    def submit_audit(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Accept the opponent's end-of-game disclosure for the mutual audit."""
        if not isinstance(payload, dict) or "records" not in payload:
            raise HandshakeRejectedError("audit payload must carry records")
        if payload.get("sender") != self._expect_role:
            raise HandshakeRejectedError(
                f"expected an audit from {self._expect_role!r}"
            )
        self.audit = payload
        return {"ok": True, "records": len(payload.get("records", []))}

    def next_turn(self) -> TurnMessage | None:
        """Pop the oldest unprocessed turn message, if any."""
        if not self.turns:
            return None
        return self.turns.pop(0)
