"""The enhanced brains: belief-driven pursuit and evasion.

These are the competition brains. They receive exactly the same
:class:`BrainView` as the blind brains - but in a real match the runtime fills
``view.target`` with the belief map's argmax instead of the true position, so
the same geometry runs on inferred knowledge. On top of the blind cores they
add barrier engineering for the cop and trap awareness for the thief.
"""

from __future__ import annotations

from ...constants import MOVE_STAY
from ..board import Cell
from ..engine import Action
from ..rules import barrier_placements
from .base import BrainView
from .blind import BlindPoliceBrain, BlindThiefBrain
from .pathfind import distance_field

#: The cop starts sealing corridors when this close to the believed target.
PINCH_RANGE = 2

#: Keep a reserve of barriers for the endgame trap.
BARRIER_RESERVE = 2


class EnhancedPoliceBrain(BlindPoliceBrain):
    """Pursue the believed cell; near it, seal escape corridors with barriers.

    The pursuit and the winning trap are inherited from the blind core. The
    addition is the pinch: when the true-path distance to the believed target
    is small and quota remains beyond the reserve, block the target's best
    escape cell instead of stepping - shrinking the thief's region instead of
    merely chasing its shadow.
    """

    def _decide_move(self, view: BrainView) -> Action:
        """Trap if possible, pinch if close, otherwise pursue."""
        if view.barriers_left > 0 and self._can_trap(view):
            return Action(move=MOVE_STAY, barrier=view.target)
        pinch = self._pinch_cell(view)
        if pinch is not None:
            return Action(move=MOVE_STAY, barrier=pinch)
        return Action(move=self._pick_move(view))

    def _pinch_cell(self, view: BrainView) -> Cell | None:
        """The escape cell worth sealing this turn, if any.

        Conditions: quota beyond the reserve, the believed target within
        :data:`PINCH_RANGE` true steps, and a legal placement that is adjacent
        to the target (an actual escape route) without being our own cell.
        Among candidates, seal the one with the most onward exits - the
        thief's widest door. Ties break in row-major order.
        """
        if view.barriers_left <= BARRIER_RESERVE:
            return None
        field = distance_field(view.board, view.target)
        our_distance = field.get(view.position, -1)
        if our_distance < 0 or our_distance > PINCH_RANGE:
            return None
        target_row, target_col = view.target
        escapes = {
            (target_row - 1, target_col),
            (target_row + 1, target_col),
            (target_row, target_col - 1),
            (target_row, target_col + 1),
        }
        candidates = [
            cell
            for cell in barrier_placements(view.board, view.position)
            if cell in escapes and cell != view.position
        ]
        if not candidates:
            return None
        return max(
            sorted(candidates),
            key=lambda cell: len(view.board.free_neighbours(cell)),
        )


class EnhancedThiefBrain(BlindThiefBrain):
    """Evade the believed cop, refusing cells the cop could seal next turn.

    Inherits the safety scoring (true distance + dead-end penalty) and adds a
    trap-risk veto: standing orthogonally adjacent to the believed cop invites
    the trapping placement, so such cells lose heavily unless nothing better
    exists.
    """

    #: Extra deduction for a cell the believed cop could trap next turn.
    TRAP_RISK_PENALTY = 3

    def _safety(self, view: BrainView, cell: Cell, field: dict[Cell, int]) -> int:
        """Blind safety score minus the trap-risk deduction."""
        score = super()._safety(view, cell, field)
        gap_row = abs(cell[0] - view.target[0])
        gap_col = abs(cell[1] - view.target[1])
        if gap_row + gap_col <= 1:
            score -= self.TRAP_RISK_PENALTY
        return score
