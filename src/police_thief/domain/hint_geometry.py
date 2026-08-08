"""Geometry helpers for judging a verbal hint against the scent field.

Parsing is deliberately modest: hints are free natural language capped at
15 words, so we extract cardinal directions only. Landmark-flavoured hints
("slipping past Times Square") carry no verifiable geometry and are treated as
uninformative rather than guessed at. This module owns that extraction plus
the scent-field motion signal (:mod:`trust` consumes both to appraise a hint).
"""

from __future__ import annotations

from .board import Cell

#: Words mapped to cardinal directions (our axis: north = row index shrinks).
_DIRECTION_WORDS = {
    "north": "N", "northern": "N", "up": "N", "upper": "N", "top": "N",
    "south": "S", "southern": "S", "down": "S", "lower": "S", "bottom": "S",
    "east": "E", "eastern": "E", "right": "E",
    "west": "W", "western": "W", "left": "W",
}

#: Cells within this fraction of the snapshot's peak count as the hot core.
_HOT_FRACTION = 0.8

#: Unit displacement of each cardinal claim (row, col); north shrinks rows.
_DIRECTION_DELTAS = {"N": (-1.0, 0.0), "S": (1.0, 0.0), "E": (0.0, 1.0), "W": (0.0, -1.0)}


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


def hot_centroid(scent: dict[Cell, float]) -> tuple[float, float] | None:
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


def mean_direction(directions: frozenset[str]) -> tuple[float, float]:
    """The average unit vector of the claimed directions."""
    deltas = [_DIRECTION_DELTAS[d] for d in sorted(directions)]
    count = len(deltas)
    return (sum(d[0] for d in deltas) / count, sum(d[1] for d in deltas) / count)
