"""Region-hunt geometry: the safe-region metric and its BFS helpers.

Split out of :mod:`region` - :func:`region_size` (and the small helpers it
leans on) is the single number several brains minimize (``region.py``,
``evade.py``, ``hybrid.py``), independent of any one brain's decision policy.
"""

from __future__ import annotations

from ..board import Board, Cell
from .pathfind import distance_field

#: Effectively-infinite distance for unreachable cells.
UNREACHABLE = 10**9

ScoreKey = tuple[int, int, int, int, str]


def _reach(field: dict[Cell, int], cell: Cell) -> int:
    """A BFS distance with the field's ``-1`` (unreachable) made infinite."""
    steps = field.get(cell, -1)
    return steps if steps >= 0 else UNREACHABLE


def _anchored(board: Board, cell: Cell) -> bool:
    """Whether a stone here extends a real cut - an edge or an existing wall."""
    row, col = cell
    if row in (0, board.size - 1) or col in (0, board.size - 1):
        return True
    neighbours = ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1))
    return any(n in board.barriers for n in neighbours)


def region_size(board: Board, cop: Cell, thief: Cell) -> int:
    """How many cells the thief reaches strictly before the cop.

    Two BFS fields; a cell belongs to the thief's safe region when its thief
    distance beats its cop distance - a cell only the thief can reach counts,
    a cell neither can reach does not. Ties go to the cop: arriving together
    is a capture. This is the single number the region cop minimizes.
    """
    cop_field = distance_field(board, cop)
    thief_field = distance_field(board, thief)
    return sum(1 for cell in thief_field if _reach(thief_field, cell) < _reach(cop_field, cell))
