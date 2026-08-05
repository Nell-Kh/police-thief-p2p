"""Hint appraisal: reading the opponent's words against the environment's testimony.

The verbal hint is the game's only deception channel - the scent map cannot
lie. This module quantifies the chapter-4 worked example: had the opponent
really walked where it claims, a fresh trail of about ``(1 - rho) * 0.9 = 0.81``
would remain there. Measured silence where the claim points, while the scent
mass sits elsewhere, exposes the hint as false; the trust coefficient attached
to the opponent's declarations drops, and the belief map damps the claimed
region instead of chasing it.

Parsing is deliberately modest: hints are free natural language capped at
15 words, so we extract cardinal directions only. Landmark-flavoured hints
("slipping past Times Square") carry no verifiable geometry and are treated as
uninformative rather than guessed at.
"""

from __future__ import annotations

from dataclasses import dataclass

from .board import Cell

VERDICT_CORROBORATED = "corroborated"
VERDICT_CONTRADICTED = "contradicted"
VERDICT_UNINFORMATIVE = "uninformative"

#: Words mapped to cardinal directions (our axis: north = row index shrinks).
_DIRECTION_WORDS = {
    "north": "N", "northern": "N", "up": "N", "upper": "N", "top": "N",
    "south": "S", "southern": "S", "down": "S", "lower": "S", "bottom": "S",
    "east": "E", "eastern": "E", "right": "E",
    "west": "W", "western": "W", "left": "W",
}

#: Trust starts neutral; corroboration pulls it up, contradiction down.
INITIAL_TRUST = 0.5
_TRUST_MEMORY = 0.7

#: Cells within this fraction of the snapshot's peak count as the hot core.
_HOT_FRACTION = 0.8

#: Minimum centroid displacement along the claim before a verdict is made.
_MOTION_EPSILON = 0.15

#: Unit displacement of each cardinal claim (row, col); north shrinks rows.
_DIRECTION_DELTAS = {"N": (-1.0, 0.0), "S": (1.0, 0.0), "E": (0.0, 1.0), "W": (0.0, -1.0)}


def _hot_centroid(scent: dict[Cell, float]) -> tuple[float, float] | None:
    """The mass-weighted center of the freshest scent - roughly, the opponent.

    Only cells near the peak participate: the stale tail of the trail would
    otherwise drag the centroid backward and blur the motion signal.
    """
    peak = max(scent.values(), default=0.0)
    if peak <= 0.0:
        return None
    hot = [(cell, value) for cell, value in scent.items() if value >= _HOT_FRACTION * peak]
    mass = sum(value for _, value in hot)
    row = sum(cell[0] * value for cell, value in hot) / mass
    col = sum(cell[1] * value for cell, value in hot) / mass
    return (row, col)


def _mean_direction(directions: frozenset[str]) -> tuple[float, float]:
    """The average unit vector of the claimed directions."""
    deltas = [_DIRECTION_DELTAS[d] for d in sorted(directions)]
    count = len(deltas)
    return (sum(d[0] for d in deltas) / count, sum(d[1] for d in deltas) / count)


@dataclass(frozen=True)
class Appraisal:
    """The outcome of judging one hint against the scent evidence."""

    directions: frozenset[str]
    region: frozenset[Cell]
    verdict: str
    factor: float


def parse_directions(hint: str) -> frozenset[str]:
    """The cardinal directions a hint mentions, if any."""
    words = hint.lower().replace("-", " ").replace(",", " ").split()
    found = {_DIRECTION_WORDS[word] for word in words if word in _DIRECTION_WORDS}
    return frozenset(found)


def region_for(directions: frozenset[str], board_size: int) -> frozenset[Cell]:
    """The board region a set of directions points at (halves intersected)."""
    half = board_size // 2
    rows = range(board_size)
    cols = range(board_size)
    if "N" in directions:
        rows = range(0, half)
    if "S" in directions:
        rows = range(board_size - half, board_size)
    if "W" in directions:
        cols = range(0, half)
    if "E" in directions:
        cols = range(board_size - half, board_size)
    if not directions:
        return frozenset()
    return frozenset((row, col) for row in rows for col in cols)


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
        centroid = _hot_centroid(scent)
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
        claim = _mean_direction(directions)
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
