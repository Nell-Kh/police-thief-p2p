"""Hint appraisal: reading the opponent's words against the environment's testimony.

The verbal hint is the game's only deception channel - the scent map cannot
lie. This module quantifies the chapter-4 worked example: had the opponent
really walked where it claims, a fresh trail of about ``(1 - rho) * 0.9 = 0.81``
would remain there. Measured silence where the claim points, while the scent
mass sits elsewhere, exposes the hint as false; the trust coefficient attached
to the opponent's declarations drops, and the belief map damps the claimed
region instead of chasing it.

Direction parsing and the scent-motion geometry live in :mod:`hint_geometry`;
this module owns the verdict and the trust coefficient built on top of them.
"""

from __future__ import annotations

from dataclasses import dataclass

from .board import Cell
from .hint_geometry import hot_centroid, mean_direction, parse_directions, region_for

VERDICT_CORROBORATED = "corroborated"
VERDICT_CONTRADICTED = "contradicted"
VERDICT_UNINFORMATIVE = "uninformative"

#: Trust starts neutral; corroboration pulls it up, contradiction down.
INITIAL_TRUST = 0.5
_TRUST_MEMORY = 0.7

#: Minimum centroid displacement along the claim before a verdict is made.
_MOTION_EPSILON = 0.15


@dataclass(frozen=True)
class Appraisal:
    """The outcome of judging one hint against the scent evidence."""

    directions: frozenset[str]
    region: frozenset[Cell]
    verdict: str
    factor: float


class TrustModel:
    """Tracks how much the opponent's words have earned to be believed."""

    def __init__(self, fresh_trail: float, board_size: int) -> None:
        """Bind the model to the locked scent yardstick and the board size.

        Args:
            fresh_trail: expected intensity of a one-turn-old trail,
                ``(1 - rho) * center`` - 0.81 under the binding parameters.
            board_size: side of the grid, for region construction.
        """
        self._yardstick = fresh_trail
        self._size = board_size
        self._trust = INITIAL_TRUST
        self._last_centroid: tuple[float, float] | None = None

    @property
    def trust(self) -> float:
        """Current trust coefficient in [0, 1]."""
        return self._trust

    def appraise(self, hint: str, scent: dict[Cell, float]) -> Appraisal:
        """Judge a hint against the *motion* of the opponent's scent field.

        Returns an :class:`Appraisal` whose ``factor`` is ready for
        ``BeliefMap.observe_region`` on the claimed region, and updates the
        trust coefficient according to the verdict. The very first appraisal
        of a game has no baseline and is always uninformative.
        """
        directions = parse_directions(hint)
        region = region_for(directions, self._size)
        centroid = hot_centroid(scent)
        previous, self._last_centroid = self._last_centroid, centroid
        if not region or previous is None or centroid is None:
            return Appraisal(directions, region, VERDICT_UNINFORMATIVE, 1.0)
        moved = (centroid[0] - previous[0], centroid[1] - previous[1])
        verdict = self._judge(moved, directions)
        self._update_trust(verdict)
        return Appraisal(directions, region, verdict, self._factor(verdict))

    def _judge(self, moved: tuple[float, float], directions: frozenset[str]) -> str:
        """Does the scent's hot centroid actually move where the hint claims?

        A single snapshot cannot verify a *motion* claim - a walk north and
        its mirrored lie leave the same cells scented (measured in phase 8:
        the snapshot judge let lies inflate our belief error 0.56 -> 2.69
        cells). The displacement of the fresh-scent centroid between
        consecutive turns can: its dot product with the claimed direction is
        positive for truth, negative for the mirror lie.
        """
        claim = mean_direction(directions)
        dot = moved[0] * claim[0] + moved[1] * claim[1]
        if dot > _MOTION_EPSILON:
            return VERDICT_CORROBORATED
        if dot < -_MOTION_EPSILON:
            return VERDICT_CONTRADICTED
        return VERDICT_UNINFORMATIVE

    def _update_trust(self, verdict: str) -> None:
        """Exponential moving average toward 1 on truth, toward 0 on lies."""
        if verdict == VERDICT_CORROBORATED:
            target = 1.0
        elif verdict == VERDICT_CONTRADICTED:
            target = 0.0
        else:
            return
        self._trust = _TRUST_MEMORY * self._trust + (1 - _TRUST_MEMORY) * target

    def _factor(self, verdict: str) -> float:
        """The region multiplier the belief map should apply for this verdict."""
        if verdict == VERDICT_CORROBORATED:
            return 1.0 + 2.0 * self._trust
        if verdict == VERDICT_CONTRADICTED:
            return 0.2 + 0.6 * self._trust
        return 1.0
