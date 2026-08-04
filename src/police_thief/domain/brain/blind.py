"""The blind-stage brains: full information, pure geometry.

Stage 3 of the development order wires a first decision core into the runtime
while the world is still fully observable - no scent, no hints, no deception.
That isolates the correctness of the decision machinery from the noise of
uncertainty: if the pursuit is wrong here, it is the geometry that is wrong,
not the inference.

Both brains are deterministic. Given the same view they always answer the same
move, so a match is reproducible step by step.
"""

from __future__ import annotations

from ...constants import MOVE_DELTAS, MOVE_ORDER, MOVE_STAY, STEPPING_MOVES
from ..board import Cell
from ..engine import Action
from .base import BrainBase, BrainView
from .pathfind import UNREACHABLE, distance_field, step_toward

#: Score deduction for standing in a cell with at most one escape route.
#: Trades a little distance for staying out of pockets the cop can seal
#: with a single barrier.
DEAD_END_PENALTY = 2


class BlindPoliceBrain(BrainBase):
    """Pursue the target along the true shortest path, trapping when possible.

    Movement: the BFS step that most shortens the real path to the target.
    Barriers: when standing orthogonally adjacent to the target with quota
    remaining, block the target's own cell - the trapping placement that wins
    the game outright.
    """

    def _pick_move(self, view: BrainView) -> str:
        """The step that most shortens the true path to the target."""
        return step_toward(view.board, view.position, view.target)

    def _decide_move(self, view: BrainView) -> Action:
        """Trap the target with a barrier when it is in reach, else pursue."""
        if view.barriers_left > 0 and self._can_trap(view):
            return Action(move=MOVE_STAY, barrier=view.target)
        return Action(move=self._pick_move(view))

    def _can_trap(self, view: BrainView) -> bool:
        """Whether the target's own cell is a legal barrier placement now."""
        row_gap = abs(view.position[0] - view.target[0])
        col_gap = abs(view.position[1] - view.target[1])
        return row_gap + col_gap == 1 and view.board.is_free(view.target)


class BlindThiefBrain(BrainBase):
    """Evade by maximising a safety score over the reachable next cells.

    The score is the true BFS distance from the pursuer, with two twists: a
    cell the pursuer cannot reach at all is the best refuge on the board, and a
    cell with at most one escape route is docked :data:`DEAD_END_PENALTY` -
    walking into a pocket hands the cop a one-barrier win. Ties break in the
    fixed move order, so the flight is reproducible.
    """

    def _pick_move(self, view: BrainView) -> str:
        """The move with the best safety score, staying put included."""
        field = distance_field(view.board, view.target)
        best_move = MOVE_STAY
        best_score = self._safety(view, view.position, field)
        for move in MOVE_ORDER:
            if move not in STEPPING_MOVES:
                continue
            candidate = self._destination(view, move)
            if candidate is None:
                continue
            score = self._safety(view, candidate, field)
            if score > best_score:
                best_move = move
                best_score = score
        return best_move

    def _safety(self, view: BrainView, cell: Cell, field: dict[Cell, int]) -> int:
        """How safe a cell is: distance from the threat, minus pocket risk."""
        base = field.get(cell, UNREACHABLE)
        if base == UNREACHABLE:
            base = view.board.size * view.board.size
        if len(view.board.free_neighbours(cell)) <= 1:
            base -= DEAD_END_PENALTY
        return base

    def _destination(self, view: BrainView, move: str) -> Cell | None:
        """Where ``move`` would land, or ``None`` if it is not playable."""
        d_row, d_col = MOVE_DELTAS[move]
        cell = (view.position[0] + d_row, view.position[1] + d_col)
        return cell if view.board.is_free(cell) else None
