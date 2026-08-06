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
        self, our_terms: dict[str, Any], our_extras: dict[str, Any], expect_role: str, reorder_window: int = 2
    ) -> None:
        """Bind the handler to our signed terms, declarations and the rival role."""
        self._our_terms = our_terms
        self._our_extras = our_extras
        self._expect_role = expect_role
        self.reorder_window = reorder_window
        self.opponent_terms: dict[str, Any] | None = None
        self.turns: list[TurnMessage] = []
        self.commitments: dict[int, str] = {}
        self.final_commit: str | None = None
        self.audit: dict[str, Any] | None = None
        self.next_step = 1
        self.buffer: dict[int, TurnMessage] = {}
        self.controls: list[dict[str, Any]] = []

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
        is_zero_step_final = (
            message.claim_response is not None
            and message.claim_response.get("caught") is True
        )
        is_legacy_final = (
            message.win_claim is not None
            and message.win_claim.get("type") == "capture"
        )

        if message.step in self.commitments:
            if message.commit == self.commitments[message.step]:
                return {"ok": True, "step": message.step}
            if not (is_zero_step_final or is_legacy_final):
                raise HandshakeRejectedError(f"step {message.step} was already committed")
            self.final_commit = message.commit
            self.turns.append(message)
            return {"ok": True, "step": message.step}

        if message.step < self.next_step:
            return {"ok": True, "step": message.step}

        self.commitments[message.step] = message.commit
        if is_zero_step_final or is_legacy_final:
            self.final_commit = message.commit

        if message.step > self.next_step + self.reorder_window:
            self.turns.append(message)
        else:
            self.buffer[message.step] = message
            while self.next_step in self.buffer:
                self.turns.append(self.buffer.pop(self.next_step))
                self.next_step += 1

        return {"ok": True, "step": message.step}

    def receive_control(self, message: dict[str, Any]) -> dict[str, Any]:
        """Queue an out-of-band control message (enable/status/restart/quit).

        Controls are signalling, not game state: they are stored for the
        runtime to read and always acknowledged - a refusal, if one is owed,
        travels back as our own control push, never as a return value.
        """
        if isinstance(message, dict):
            self.controls.append(message)
        return {"ok": True}

    def next_control(self) -> dict[str, Any] | None:
        """Pop the oldest unread control message, if any."""
        if not self.controls:
            return None
        return self.controls.pop(0)

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
