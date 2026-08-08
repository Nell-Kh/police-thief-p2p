"""The replay session: a saved match walked step by step, verified live.

This is the Replay Viewer's engine, kept out of the GUI so it is fully
testable: it loads a saved logbook, orders the revealed turns, reconstructs the
board at every step, and re-verifies each record against its commitment as the
user steps through - the ch. 7 flow, over the *full* sealed record as ch. 5
demands, not the simplified nonce|move sketch. One TAMPERED voids the match.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .audit import VERDICT_OK, VERDICT_TAMPERED
from .crypto import verify
from .logbook import Logbook
from .sealing import revealed_position
from .state_summary import grid_size_of, parse_barriers

__all__ = ["ReplaySession", "grid_size_of", "parse_barriers"]


class ReplaySession:
    """One saved match, navigable forward and backward, verified per step."""

    def __init__(self, book: Logbook) -> None:
        """Open a session over a loaded logbook."""
        self.book = book
        self.turns = sorted(
            (record for record in book.records if record["payload"].get("type") == "turn"),
            key=lambda record: record["payload"].get("step", 0),
        )
        self.index = 0

    @classmethod
    def load(cls, path: str | Path) -> ReplaySession:
        """Open a session straight from a ``log_<game_id>_gNN.json`` file."""
        return cls(Logbook.load(path))

    @property
    def current(self) -> dict[str, Any] | None:
        """The record under the cursor, or ``None`` for an empty log."""
        if not self.turns:
            return None
        return self.turns[self.index]

    def forward(self) -> int:
        """Step toward the end of the match; the cursor stops at the last turn."""
        if self.index < len(self.turns) - 1:
            self.index += 1
        return self.index

    def back(self) -> int:
        """Step toward the start; the cursor stops at the first turn."""
        if self.index > 0:
            self.index -= 1
        return self.index

    def verdict_for(self, record: dict[str, Any]) -> str:
        """Re-verify one record: the comparison is binary, never 'almost'."""
        try:
            ok = verify(record["payload"], record["nonce"], record["commit"])
        except (KeyError, TypeError):
            ok = False
        return VERDICT_OK if ok else VERDICT_TAMPERED

    def current_verdict(self) -> str:
        """The stamp for the step under the cursor."""
        record = self.current
        return VERDICT_OK if record is None else self.verdict_for(record)

    def overall_verdict(self) -> str:
        """The whole match's stamp: one failed step voids everything."""
        for record in self.book.records:
            if self.verdict_for(record) == VERDICT_TAMPERED:
                return VERDICT_TAMPERED
        return VERDICT_OK

    def scene(self) -> dict[str, Any]:
        """Everything the viewer draws for the current step."""
        record = self.current
        if record is None:
            return {"step": 0, "position": None, "barriers": [], "grid": 0,
                    "hint": "", "verdict": VERDICT_OK}
        payload = record["payload"]
        return {
            "step": payload.get("step", 0),
            "position": revealed_position(payload),
            "barriers": parse_barriers(str(payload.get("state", ""))),
            "grid": grid_size_of(str(payload.get("state", ""))),
            "hint": str(payload.get("hint", "")),
            "verdict": self.verdict_for(record),
        }
