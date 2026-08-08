"""De-duplication and reordering of one opponent's incoming turn stream.

Split out of :mod:`inbound` - buffering turns that arrive out of order and
refusing a second commitment for an already-sealed step is a self-contained
concern, independent of negotiation, controls or the end-of-game audit.
"""

from __future__ import annotations

from ..domain.turnmsg import TurnMessage


class HandshakeRejectedError(RuntimeError):
    """Raised when the opponent's terms or turn stream do not match ours."""


class TurnReorderBuffer:
    """Accepts already-authenticated turn messages, de-duplicated and in order."""

    def __init__(self, reorder_window: int = 2) -> None:
        """Bind the buffer to how many steps ahead may arrive before flushing."""
        self.reorder_window = reorder_window
        self.commitments: dict[int, str] = {}
        self.final_commit: str | None = None
        self.next_step = 1
        self.buffer: dict[int, TurnMessage] = {}
        self.turns: list[TurnMessage] = []

    def accept(self, message: TurnMessage) -> dict[str, object]:
        """Record one turn message; receiving it makes it our turn.

        A second commitment for the same step is refused - once sealed, a move
        cannot be replaced - unless it carries the final claim-response or
        win-claim that legitimately closes out the mini-game.
        """
        is_zero_step_final = (
            message.claim_response is not None
            and message.claim_response.get("caught") is True
        )
        is_legacy_final = (
            message.win_claim is not None and message.win_claim.get("type") == "capture"
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

    def pop(self) -> TurnMessage | None:
        """Pop the oldest unprocessed turn message, if any."""
        if not self.turns:
            return None
        return self.turns.pop(0)
