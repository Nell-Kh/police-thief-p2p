"""The wall cop: split the board first, hunt second.

Round two of the phase-8 arms race. The region cop (``region.py``) converts
every start against reactive evaders, but the notebook's strongest thief -
which weighs its own safe region, distance AND openness - orbits the open
board and survives it 60/72. No greedy refinement fixed that; the classic
pursuit-theory answer did: spend the opening on a **center wall** with a
single door, cutting the 7x7 into two halves. Wall building needs no
knowledge of the thief's position at all - ideal under belief uncertainty -
and once the halves exist, the inherited region hunt finishes inside the
thief's half, door under control. Exhaustive result: 1900/1900 captures
against every thief archetype in the zoo, max 29 of 35 steps, max 8 of 14
barriers.
"""

from __future__ import annotations

from ...constants import MOVE_STAY
from ..board import Board, Cell
from ..engine import Action
from .base import BrainView
from .pathfind import step_toward
from .region import RegionPoliceBrain

#: The column the opening wall fills (the board's central column).
WALL_COLUMN = 3

#: The one cell left open - the guarded door between the halves.
DOOR = (3, 3)

#: Wall build order: edges inward, so every stone anchors an existing cut.
WALL_ROWS = (0, 1, 2, 4, 5, 6)


class WallPoliceBrain(RegionPoliceBrain):
    """Opening-book wall builder on top of the region hunter.

    Stateless on purpose: the next missing stone is re-derived from the
    board every turn, so a restarted or resumed game continues the same
    plan without any carried memory.
    """

    def _decide_move(self, view: BrainView) -> Action:
        """Trap if offered; otherwise build the wall; then hunt by region."""
        if view.barriers_left > 0 and self._can_trap(view):
            return Action(move=MOVE_STAY, barrier=view.target)
        build = self._build_action(view)
        if build is not None:
            return build
        return super()._decide_move(view)

    def _build_action(self, view: BrainView) -> Action | None:
        """The next wall step: place the missing stone, or walk toward it.

        Returns None once the wall is complete (or quota-exhausted), handing
        control to the region hunt. A stone whose cell holds the believed
        thief is never placed blind - the adjacent-trap rule above already
        covers the case where that belief is right.
        """
        stone = self._next_wall_stone(view)
        if stone is None or view.barriers_left <= 0:
            return None
        gap = abs(view.position[0] - stone[0]) + abs(view.position[1] - stone[1])
        if gap == 1 and stone != view.target:
            return Action(move=MOVE_STAY, barrier=stone)
        move = step_toward(view.board, view.position, self._build_spot(view, stone))
        if move != MOVE_STAY:
            return Action(move=move)
        return None  # boxed in - never donate a turn, hunt instead

    def _next_wall_stone(self, view: BrainView) -> Cell | None:
        """The first wall cell still free (skipping the door and our own cell)."""
        for row in WALL_ROWS:
            cell = (row, WALL_COLUMN)
            if view.board.is_free(cell) and cell != view.position:
                return cell
        return None

    def _build_spot(self, view: BrainView, stone: Cell) -> Cell:
        """A free cell adjacent to the stone to build from, own side preferred."""
        row, col = stone
        side = -1 if view.position[1] <= col else 1
        for candidate in ((row, col + side), (row, col - side), (row - 1, col), (row + 1, col)):
            if view.board.in_bounds(candidate) and view.board.is_free(candidate):
                return candidate
        return stone


def wall_progress(board: Board) -> int:
    """How many of the six wall stones are placed (observability for the GUI)."""
    return sum(1 for row in WALL_ROWS if (row, WALL_COLUMN) in board.barriers)
