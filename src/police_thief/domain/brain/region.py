"""The region cop: shrink the thief's safe region until nothing is left.

Born in the phase-8 research notebook. The pinch cop (``enhanced.py``)
converts 0/72 starts even with perfect information - pure pursuit on a grid
with equal speeds is a parity dance, and reactive pinches never fire at the
diagonal where the dance settles. The cure is to stop chasing the thief and
start strangling its *options*: every turn, minimize the number of cells the
thief can reach before the cop (its safe region), tie-broken by the thief's
exit count and then by closing distance. A barrier must starve the region by
:attr:`RegionPoliceBrain.MIN_SHRINK` cells in the mid-game - quota is finite -
but once the region is down to :attr:`RegionPoliceBrain.ENDGAME` cells, any
exit sealed is progress the thief can never undo. Result on the same 72
starts: 72 captures, mean 9 steps, ~1 barrier.
"""

from __future__ import annotations

from ...constants import MOVE_STAY
from ..board import Board, Cell
from ..engine import Action
from ..rules import barrier_placements, destination, legal_steps
from .base import BrainView
from .blind import BlindPoliceBrain
from .pathfind import distance_field

#: Effectively-infinite distance for unreachable cells.
UNREACHABLE = 10**9

ScoreKey = tuple[int, int, int, int, str]


def _reach(field: dict[Cell, int], cell: Cell) -> int:
    """A BFS distance with the field's ``-1`` (unreachable) made infinite."""
    steps = field.get(cell, -1)
    return steps if steps >= 0 else UNREACHABLE


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


class RegionPoliceBrain(BlindPoliceBrain):
    """Greedy minimizer of the thief's safe region, exits and distance."""

    #: Mid-game gate: a barrier must shrink the region by this many cells.
    MIN_SHRINK = 3

    #: Region size at which every sealed exit is worth a barrier.
    ENDGAME = 4

    def _decide_move(self, view: BrainView) -> Action:
        """Trap when adjacent; otherwise the option with the best score key."""
        if view.barriers_left > 0 and self._can_trap(view):
            return Action(move=MOVE_STAY, barrier=view.target)
        options = self._move_options(view) + self._barrier_options(view)
        return min(options)[1]

    def _move_options(self, view: BrainView) -> list[tuple[ScoreKey, Action]]:
        """Every displacing step, scored on the board as it stands.

        A move never changes the thief's exits, so the current exit count is
        the tie-break; ``STAY`` is deliberately absent - a cop that neither
        moves nor builds is donating a turn to the parity dance.
        """
        exits_now = len(view.board.free_neighbours(view.target))
        options: list[tuple[ScoreKey, Action]] = []
        for move in legal_steps(view.board, view.position):
            position = destination(view.position, move)
            size = region_size(view.board, position, view.target)
            distance = _reach(distance_field(view.board, view.target), position)
            options.append(((size, exits_now, distance, 0, str(move)), Action(move=move)))
        return options

    def _barrier_options(self, view: BrainView) -> list[tuple[ScoreKey, Action]]:
        """Every worthwhile placement, scored on a trial board.

        Worthwhile means a :attr:`MIN_SHRINK` region cut, or - inside the
        endgame - any reduction of the thief's exit count. The barrier flag in
        the key makes an equally-scored move win: quota is the scarcer coin.
        """
        if view.barriers_left <= 0:
            return []
        here = region_size(view.board, view.position, view.target)
        exits_now = len(view.board.free_neighbours(view.target))
        options: list[tuple[ScoreKey, Action]] = []
        for cell in barrier_placements(view.board, view.position):
            if cell in (view.position, view.target):
                continue
            trial = Board(view.board.size, set(view.board.barriers) | {cell})
            size = region_size(trial, view.position, view.target)
            exits = len(trial.free_neighbours(view.target))
            worthwhile = size <= here - self.MIN_SHRINK or (
                here <= self.ENDGAME and exits < exits_now
            )
            if not worthwhile:
                continue
            distance = _reach(distance_field(trial, view.target), view.position)
            options.append(
                ((size, exits, distance, 1, str(cell)), Action(move=MOVE_STAY, barrier=cell))
            )
        return options
