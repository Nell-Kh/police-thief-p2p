"""Barrier-aware shortest paths on the board.

Plain Manhattan distance lies as soon as barriers appear: two adjacent cells can
be a long detour apart. A breadth-first distance field over the *actual* board
gives the true step count, and because every edge costs one step, BFS is exact
here - no heuristic needed (PRD_strategy, FR on barrier-aware distances).

Everything is deterministic: neighbours are expanded in the fixed move order, so
both peers - and every replay - compute identical fields.
"""

from __future__ import annotations

from collections import deque

from ...constants import MOVE_DELTAS, MOVE_ORDER, MOVE_STAY, STEPPING_MOVES
from ..board import Board, Cell

#: Distance assigned to cells no path reaches (walled off or barrier cells).
UNREACHABLE = -1


def distance_field(board: Board, source: Cell) -> dict[Cell, int]:
    """True step distances from ``source`` to every cell, respecting barriers.

    Args:
        board: the board whose barriers constrain movement.
        source: the cell distances are measured from.

    Returns:
        A mapping of every board cell to its distance in steps, with
        :data:`UNREACHABLE` for cells no path reaches. The source itself is 0
        (or unreachable if it is a barrier cell).
    """
    field: dict[Cell, int] = dict.fromkeys(board.cells(), UNREACHABLE)
    if not board.is_free(source):
        return field
    field[source] = 0
    queue: deque[Cell] = deque([source])
    while queue:
        current = queue.popleft()
        for neighbour in board.free_neighbours(current):
            if field[neighbour] == UNREACHABLE:
                field[neighbour] = field[current] + 1
                queue.append(neighbour)
    return field


def distance(board: Board, source: Cell, target: Cell) -> int:
    """True step distance between two cells, or :data:`UNREACHABLE`."""
    return distance_field(board, source).get(target, UNREACHABLE)


def step_toward(board: Board, start: Cell, target: Cell) -> str:
    """The move that best shortens the true path from ``start`` to ``target``.

    Distances are computed *from the target*, so one field prices every
    candidate destination. Ties break in the fixed move order; if no step
    improves on standing still - or the target is unreachable - ``STAY``.
    """
    field = distance_field(board, target)
    best_move = MOVE_STAY
    best_score = field.get(start, UNREACHABLE)
    if best_score == UNREACHABLE:
        return MOVE_STAY
    for move in MOVE_ORDER:
        if move not in STEPPING_MOVES:
            continue
        d_row, d_col = MOVE_DELTAS[move]
        candidate = (start[0] + d_row, start[1] + d_col)
        if not board.is_free(candidate):
            continue
        score = field[candidate]
        if score != UNREACHABLE and score < best_score:
            best_move = move
            best_score = score
    return best_move


def step_away(board: Board, start: Cell, threat: Cell) -> str:
    """The move that best lengthens the true path from ``threat``.

    Used by the evader: among the legal options (staying included), pick the
    destination whose BFS distance from the threat is greatest, breaking ties in
    the fixed move order. Cells the threat cannot reach at all are the best
    refuge of all.
    """
    field = distance_field(board, threat)

    def score(cell: Cell) -> int:
        value = field.get(cell, UNREACHABLE)
        return board.size * board.size if value == UNREACHABLE else value

    best_move = MOVE_STAY
    best_score = score(start)
    for move in MOVE_ORDER:
        if move not in STEPPING_MOVES:
            continue
        d_row, d_col = MOVE_DELTAS[move]
        candidate = (start[0] + d_row, start[1] + d_col)
        if not board.is_free(candidate):
            continue
        if score(candidate) > best_score:
            best_move = move
            best_score = score(candidate)
    return best_move
