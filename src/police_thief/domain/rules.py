"""The physical laws of the race, enforced locally by each agent.

There is no referee: both peers run this same rule set over a byte-identical
contract, so they compute the same legality decisions independently. Every
function here is pure - it inspects a board and returns a verdict.

Rules implemented (rulebook ch. 3.4):

* one move per turn: a single orthogonal step, or stay in place;
* **no diagonals** - a diagonal move cannot even be expressed;
* a barrier may only be placed on a turn in which the cop forgoes movement,
  only on the cop's own cell or one of its four orthogonal neighbours, and only
  while the barrier quota has not been exhausted;
* a barrier placed on the thief's cell captures the thief;
* a thief with no legal step at all is likewise captured.
"""

from __future__ import annotations

from ..constants import MOVE_DELTAS, MOVE_ORDER, MOVE_STAY, STEPPING_MOVES
from .board import Board, Cell


class IllegalMoveError(ValueError):
    """Raised when an agent attempts a move the rules forbid."""


class IllegalBarrierError(ValueError):
    """Raised when a barrier placement violates the barrier law."""


def destination(cell: Cell, move: str) -> Cell:
    """The cell an agent reaches by applying ``move`` to ``cell``.

    Raises:
        IllegalMoveError: if ``move`` is not one of the five legal moves. Diagonal
            moves are unrepresentable, so they surface here.
    """
    if move not in MOVE_DELTAS:
        raise IllegalMoveError(f"unknown move {move!r}; legal moves are {MOVE_ORDER}")
    d_row, d_col = MOVE_DELTAS[move]
    row, col = cell
    return (row + d_row, col + d_col)


def is_legal_move(board: Board, cell: Cell, move: str) -> bool:
    """Whether an agent standing on ``cell`` may perform ``move``."""
    try:
        target = destination(cell, move)
    except IllegalMoveError:
        return False
    return board.is_free(target)


def legal_moves(board: Board, cell: Cell) -> list[str]:
    """Every legal move from ``cell``, in the deterministic tie-break order.

    Staying is legal whenever the agent's own cell is free, which it always is
    while the agent stands on it.
    """
    return [move for move in MOVE_ORDER if is_legal_move(board, cell, move)]


def legal_steps(board: Board, cell: Cell) -> list[str]:
    """The legal moves that actually displace the agent (``STAY`` excluded)."""
    return [move for move in legal_moves(board, cell) if move in STEPPING_MOVES]


def validate_move(board: Board, cell: Cell, move: str) -> Cell:
    """Check a move and return its destination.

    Raises:
        IllegalMoveError: if the move is unknown or would leave the board or enter a
            barrier. This is what an agent calls on a move announced by the
            opponent, since each side enforces the physics on the other.
    """
    target = destination(cell, move)
    if not board.in_bounds(target):
        raise IllegalMoveError(f"move {move} from {cell} leaves the board")
    if board.is_barrier(target):
        raise IllegalMoveError(f"move {move} from {cell} enters barrier {target}")
    return target


def is_trapped(board: Board, cell: Cell) -> bool:
    """Whether an agent on ``cell`` has no legal step at all.

    Staying does not count as an escape: the rulebook treats a thief with no
    legal move whatsoever - every neighbour blocked by barriers or by the board
    edge - as captured.
    """
    return not legal_steps(board, cell)


def barrier_placements(board: Board, cop: Cell) -> list[Cell]:
    """The cells on which the cop may place a barrier this turn.

    That is the cop's own cell plus its four orthogonal neighbours, minus cells
    that are off-board or already blocked.
    """
    candidates = [cop, *board.neighbours(cop)]
    return [cell for cell in candidates if board.is_free(cell)]


def validate_barrier(
    board: Board,
    cop: Cell,
    cell: Cell,
    move: str,
    used: int,
    quota: int,
) -> None:
    """Check a barrier placement against the barrier law.

    Args:
        board: the board the barrier would be placed on.
        cop: the cop's current cell.
        cell: the cell the cop wants to block.
        move: the move the cop declared this turn; must be ``STAY``.
        used: how many barriers the cop has already placed.
        quota: the maximum number of barriers allowed.

    Raises:
        IllegalBarrierError: if the cop moved this turn, exhausted the quota, or
            targeted a cell that is not within one step, is off-board, or is
            already blocked.
    """
    if move != MOVE_STAY:
        raise IllegalBarrierError("a barrier may only be placed on a turn without movement")
    if used >= quota:
        raise IllegalBarrierError(f"barrier quota exhausted ({used}/{quota})")
    if cell not in barrier_placements(board, cop):
        raise IllegalBarrierError(f"barrier {cell} is not a free cell within one step of {cop}")
