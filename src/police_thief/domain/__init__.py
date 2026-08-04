"""Pure game logic: board, rules, scoring, state and the turn engine.

Nothing in this package performs I/O. Every module is deterministic and free of
side effects apart from mutating the :class:`GameState` handed to it, which is
what makes the whole rule set replayable and cryptographically auditable.
"""

from .board import Board, BoardError, Cell
from .engine import Action, Engine
from .rules import IllegalBarrierError, IllegalMoveError
from .scoring import Outcome
from .state import GameState

__all__ = [
    "Action",
    "Board",
    "BoardError",
    "Cell",
    "Engine",
    "GameState",
    "IllegalBarrierError",
    "IllegalMoveError",
    "Outcome",
]
