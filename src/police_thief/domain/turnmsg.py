"""The per-turn wire message - what actually crosses the network.

Following ADR-7 and the reference implementation: true position, move and
intent are NOT here in the clear. A turn message carries only the sealed
commitment hash, the natural-language hint, the sender's scent grid, and the
public events the rules require to be open - a barrier declaration, a capture
claim, its truthful answer, or a survival claim. The turn token travels with
the message: receiving one makes it your turn.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..constants import ROLES
from .board import Cell


class TurnMessageError(ValueError):
    """Raised when an incoming turn message is malformed."""


def encode_scent(snapshot: dict[Cell, float]) -> dict[str, float]:
    """Scent grid to wire form: ``{"row,col": intensity}`` for noisy cells."""
    return {f"{row},{col}": value for (row, col), value in snapshot.items() if value > 0.0}


def decode_scent(wire: dict[str, Any]) -> dict[Cell, float]:
    """Wire form back to cells, refusing anything unparseable."""
    decoded: dict[Cell, float] = {}
    for key, value in wire.items():
        try:
            row_text, col_text = key.split(",")
            decoded[(int(row_text), int(col_text))] = float(value)
        except (ValueError, TypeError) as error:
            raise TurnMessageError(f"bad scent cell {key!r}: {error}") from error
    return decoded


@dataclass(frozen=True)
class TurnMessage:
    """One turn on the wire. Optional fields are the public events."""

    step: int
    sender: str
    hint: str
    smell_grid: dict[str, float]
    commit: str
    barrier_placed: list[int] | None = None
    capture_claim: list[int] | None = None
    claim_response: dict[str, Any] | None = None
    win_claim: dict[str, Any] | None = None
    extras: dict[str, Any] = field(default_factory=dict)

    def to_wire(self) -> dict[str, Any]:
        """The JSON-ready dict sent to the opponent's ``receive_turn`` tool."""
        wire: dict[str, Any] = {
            "step": self.step,
            "sender": self.sender,
            "hint": self.hint,
            "smell_grid": dict(self.smell_grid),
            "commit": self.commit,
            "barrier_placed": self.barrier_placed,
            "capture_claim": self.capture_claim,
            "claim_response": self.claim_response,
            "win_claim": self.win_claim,
        }
        wire.update(self.extras)
        return wire

    @classmethod
    def from_wire(cls, wire: dict[str, Any]) -> TurnMessage:
        """Parse and validate an incoming turn message.

        Raises:
            TurnMessageError: on a missing field, unknown sender, negative
                step, empty commitment, or any cleartext position field - a
                peer never acts on a message it does not fully understand.
        """
        if not isinstance(wire, dict):
            raise TurnMessageError("turn message must be an object")
        for name in ("step", "sender", "hint", "smell_grid", "commit"):
            if name not in wire:
                raise TurnMessageError(f"turn message missing field {name!r}")
        if wire["sender"] not in ROLES:
            raise TurnMessageError(f"unknown sender {wire['sender']!r}")
        try:
            step = int(wire["step"])
        except (TypeError, ValueError) as error:
            raise TurnMessageError(f"step must be an integer, got {wire['step']!r}") from error
        if step < 0:
            raise TurnMessageError(f"step must not be negative, got {step}")
        if not str(wire["commit"]):
            raise TurnMessageError("commit hash must not be empty")
        if not isinstance(wire["smell_grid"], dict):
            raise TurnMessageError("smell_grid must be a mapping")
        decode_scent(wire["smell_grid"])  # validates the keys and values
        for forbidden in ("position", "move", "intent"):
            if forbidden in wire:
                raise TurnMessageError(
                    f"turn message must not carry {forbidden!r} in cleartext"
                )
        known = {
            "step", "sender", "hint", "smell_grid", "commit",
            "barrier_placed", "capture_claim", "claim_response", "win_claim",
        }
        extras = {key: value for key, value in wire.items() if key not in known}
        return cls(
            step=step,
            sender=str(wire["sender"]),
            hint=str(wire["hint"]),
            smell_grid=dict(wire["smell_grid"]),
            commit=str(wire["commit"]),
            barrier_placed=_cell_or_none(wire.get("barrier_placed")),
            capture_claim=_cell_or_none(wire.get("capture_claim")),
            claim_response=wire.get("claim_response"),
            win_claim=wire.get("win_claim"),
            extras=extras,
        )


def _cell_or_none(value: Any) -> list[int] | None:
    """Validate an optional public cell field."""
    if value is None:
        return None
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise TurnMessageError(f"cell field must be [row, col], got {value!r}")
    try:
        return [int(value[0]), int(value[1])]
    except (TypeError, ValueError) as error:
        raise TurnMessageError(f"cell field must hold integers, got {value!r}") from error
