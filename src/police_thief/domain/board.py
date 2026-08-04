"""The game board: a discrete grid with permanent, impassable barriers.

Geometry follows ADR-4 and the rulebook's chapter-3 default: a cell is a
``(row, col)`` pair, ``(0, 0)`` sits in the top-left corner and the row index
grows downward. The board knows nothing about agents, turns or scoring - it only
answers questions about geometry and passability.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator

from ..constants import MOVE_DELTAS, STEPPING_MOVES

Cell = tuple[int, int]


class BoardError(ValueError):
    """Raised when an operation would violate the board's geometry."""


class Board:
    """A square grid of ``size`` x ``size`` cells with a set of barriers.

    Barriers are irreversible: once a cell is blocked it stays blocked for the
    rest of the game, and it is impassable to *both* players.
    """

    def __init__(self, size: int, barriers: Iterable[Cell] = ()) -> None:
        """Create a board.

        Args:
            size: side length of the square grid; must be positive.
            barriers: cells already blocked at creation time.

        Raises:
            BoardError: if the size is not positive or a barrier is off-board.
        """
        if size <= 0:
            raise BoardError(f"board size must be positive, got {size}")
        self._size = size
        self._barriers: set[Cell] = set()
        for cell in barriers:
            self.place_barrier(cell)

    @property
    def size(self) -> int:
        """Side length of the grid."""
        return self._size

    @property
    def barriers(self) -> frozenset[Cell]:
        """The blocked cells, as an immutable snapshot."""
        return frozenset(self._barriers)

    def in_bounds(self, cell: Cell) -> bool:
        """Whether a cell lies inside the grid."""
        row, col = cell
        return 0 <= row < self._size and 0 <= col < self._size

    def is_barrier(self, cell: Cell) -> bool:
        """Whether a cell is blocked by a barrier."""
        return cell in self._barriers

    def is_free(self, cell: Cell) -> bool:
        """Whether a cell is on the board and not blocked.

        Agent occupancy is deliberately ignored: an agent may step onto the cell
        the opponent occupies - that overlap is exactly how a capture happens.
        """
        return self.in_bounds(cell) and not self.is_barrier(cell)

    def place_barrier(self, cell: Cell) -> None:
        """Block a cell permanently.

        Raises:
            BoardError: if the cell is off-board or already blocked.
        """
        if not self.in_bounds(cell):
            raise BoardError(f"barrier {cell} is outside a {self._size}x{self._size} board")
        if cell in self._barriers:
            raise BoardError(f"barrier {cell} is already placed; barriers are irreversible")
        self._barriers.add(cell)

    def neighbours(self, cell: Cell) -> list[Cell]:
        """The on-board orthogonal neighbours of a cell, barriers included."""
        row, col = cell
        candidates = ((row + d_row, col + d_col) for d_row, d_col in _STEP_DELTAS)
        return [neighbour for neighbour in candidates if self.in_bounds(neighbour)]

    def free_neighbours(self, cell: Cell) -> list[Cell]:
        """The on-board orthogonal neighbours that are not blocked."""
        return [neighbour for neighbour in self.neighbours(cell) if not self.is_barrier(neighbour)]

    def cells(self) -> Iterator[Cell]:
        """Iterate over every cell of the grid, row by row."""
        for row in range(self._size):
            for col in range(self._size):
                yield (row, col)

    def copy(self) -> Board:
        """An independent copy, so look-ahead search cannot mutate the real board."""
        return Board(self._size, self._barriers)

    def __repr__(self) -> str:
        """Developer-facing summary."""
        return f"Board(size={self._size}, barriers={len(self._barriers)})"


#: Displacements of the four stepping moves, resolved once at import time.
_STEP_DELTAS: tuple[tuple[int, int], ...] = tuple(MOVE_DELTAS[move] for move in STEPPING_MOVES)
