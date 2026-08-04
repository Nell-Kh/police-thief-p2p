"""The Bayesian belief map: where do I think my opponent is?

Neither side ever sees the other's position. Each peer holds a probability
matrix over the board - P(opponent at cell) - updated every turn from the
evidence it may legally read: the opponent's transmitted scent field, public
events (barriers, failed capture claims), and, through the trust layer, the
verbal hint. The chapter-6 policy then targets the argmax.

The core update matches the reference implementation for behavioural
compatibility - diffuse with the motion model, multiply by ``1 + w * tau``,
normalize - and adds what the reference leaves unused: barrier-aware diffusion,
exclusion on a truthfully answered "not caught", and a hook for hint evidence.
"""

from __future__ import annotations

from collections.abc import Iterable

from .board import Board, Cell

#: Default weight of scent evidence, matching the reference implementation.
DEFAULT_SCENT_TRUST = 4.0


class BeliefMap:
    """A normalized probability distribution over the opponent's cell."""

    def __init__(self, board: Board, scent_trust: float = DEFAULT_SCENT_TRUST) -> None:
        """Start uniform over every free cell of ``board``.

        The board reference is live: barriers placed later automatically
        constrain diffusion, and newly blocked cells are zeroed on update.
        """
        self._board = board
        self._scent_trust = scent_trust
        self._probs: dict[Cell, float] = {}
        self.reset()

    def reset(self) -> None:
        """Forget everything: uniform belief over the currently free cells."""
        free = [cell for cell in self._board.cells() if not self._board.is_barrier(cell)]
        weight = 1.0 / len(free)
        self._probs = dict.fromkeys(free, weight)

    def probability(self, cell: Cell) -> float:
        """P(opponent at ``cell``); zero for barriers and off-board cells."""
        return self._probs.get(cell, 0.0)

    def snapshot(self) -> dict[Cell, float]:
        """A copy of the full distribution - what the GUI heatmap renders."""
        return dict(self._probs)

    def argmax(self) -> Cell:
        """The most likely opponent cell, ties broken in row-major order."""
        return max(sorted(self._probs), key=lambda cell: self._probs[cell])

    def diffuse(self) -> None:
        """Spread each cell's mass over the moves the opponent could have made.

        The motion model is the legal move set: stay, or one orthogonal step
        into a free cell. Barriers and board edges receive no mass, so the
        belief respects the physics automatically.
        """
        spread: dict[Cell, float] = {}
        for cell, mass in self._probs.items():
            if mass == 0.0:
                continue
            targets = [cell, *self._board.free_neighbours(cell)]
            share = mass / len(targets)
            for target in targets:
                spread[target] = spread.get(target, 0.0) + share
        self._probs = spread
        self._normalize()

    def observe_scent(self, scent: dict[Cell, float]) -> None:
        """Fold the opponent's transmitted scent field into the belief.

        Each cell's probability is scaled by ``1 + trust * tau`` - fresh scent
        concentrates the mass, quiet cells keep only their prior.
        """
        for cell in self._probs:
            tau = scent.get(cell, 0.0)
            if tau > 0.0:
                self._probs[cell] *= 1.0 + self._scent_trust * tau
        self._normalize()

    def observe_region(self, cells: Iterable[Cell], factor: float) -> None:
        """Scale a region's likelihood - the hook the hint layer drives.

        ``factor > 1`` boosts the region (a trusted hint pointing there);
        ``0 <= factor < 1`` damps it (a hint judged to be a lie).
        """
        if factor < 0:
            raise ValueError(f"factor must not be negative, got {factor}")
        for cell in cells:
            if cell in self._probs:
                self._probs[cell] *= factor
        self._normalize()

    def exclude(self, cell: Cell) -> None:
        """Rule a cell out - e.g. after a truthful "not caught" answer.

        The reference implementation discards this negative evidence; using it
        is one of our planned edges.
        """
        if cell in self._probs:
            self._probs[cell] = 0.0
        self._normalize()

    def _normalize(self) -> None:
        """Keep the distribution summing to one and off barrier cells.

        If every hypothesis has been eliminated - contradictory evidence -
        the honest move is to admit ignorance and reset to uniform.
        """
        for cell in list(self._probs):
            if self._board.is_barrier(cell):
                self._probs[cell] = 0.0
        total = sum(self._probs.values())
        if total <= 0.0:
            self.reset()
            return
        for cell in self._probs:
            self._probs[cell] /= total
