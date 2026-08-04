"""The state of a single mini-game.

The state object is what a peer holds locally about the *objective* board:
positions, barriers, the step counter and the outcome once the game ends. What
an agent is allowed to *see* of the opponent is a separate concern (belief maps
and scent), handled elsewhere - this class is the ground truth used by the
engine and by the replay verifier.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..constants import ROLE_POLICE, ROLE_THIEF
from ..shared.schema import GameContract
from .board import Board, Cell
from .scoring import Outcome


@dataclass
class GameState:
    """Ground truth of one mini-game in progress."""

    board: Board
    cop: Cell
    thief: Cell
    step: int = 0
    barriers_used: int = 0
    outcome: Outcome | None = None
    history: list[str] = field(default_factory=list)

    @classmethod
    def from_contract(cls, contract: GameContract) -> GameState:
        """Start a fresh mini-game from the signed contract's opening setup."""
        board = Board(contract.board.grid_size)
        return cls(board=board, cop=contract.board.cop_start, thief=contract.board.thief_start)

    @property
    def finished(self) -> bool:
        """Whether the mini-game has ended."""
        return self.outcome is not None

    def position_of(self, role: str) -> Cell:
        """The current cell of ``role``."""
        if role == ROLE_POLICE:
            return self.cop
        if role == ROLE_THIEF:
            return self.thief
        raise ValueError(f"unknown role {role!r}")

    def set_position(self, role: str, cell: Cell) -> None:
        """Move ``role`` to ``cell``."""
        if role == ROLE_POLICE:
            self.cop = cell
        elif role == ROLE_THIEF:
            self.thief = cell
        else:
            raise ValueError(f"unknown role {role!r}")

    def overlapping(self) -> bool:
        """Whether both agents occupy the same cell - i.e. a capture happened."""
        return self.cop == self.thief

    def barriers_left(self, contract: GameContract) -> int:
        """How many barriers the cop may still place."""
        return max(0, contract.movement.max_barriers - self.barriers_used)

    def record(self, entry: str) -> None:
        """Append a human-readable line to the game's narrative history."""
        self.history.append(entry)
