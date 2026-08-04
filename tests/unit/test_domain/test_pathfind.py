"""Tests for barrier-aware BFS pathfinding."""

from __future__ import annotations

from police_thief.domain.board import Board
from police_thief.domain.brain.pathfind import (
    UNREACHABLE,
    distance,
    distance_field,
    step_away,
    step_toward,
)


def test_the_source_is_at_distance_zero() -> None:
    assert distance_field(Board(7), (3, 3))[(3, 3)] == 0


def test_distances_grow_by_one_per_step() -> None:
    field = distance_field(Board(7), (0, 0))
    assert field[(0, 1)] == 1
    assert field[(1, 1)] == 2
    assert field[(6, 6)] == 12


def test_on_an_open_board_bfs_equals_manhattan() -> None:
    field = distance_field(Board(7), (3, 3))
    for cell, value in field.items():
        assert value == abs(cell[0] - 3) + abs(cell[1] - 3)


def test_a_wall_forces_a_detour() -> None:
    """This is exactly where raw Manhattan distance lies."""
    wall = [(0, 1), (1, 1), (2, 1)]
    board = Board(7, wall)
    assert distance(board, (0, 0), (0, 2)) == 8
    assert abs(0 - 0) + abs(0 - 2) == 2


def test_a_walled_off_region_is_unreachable() -> None:
    pocket_walls = [(0, 1), (1, 0), (1, 1)]
    board = Board(7, pocket_walls)
    assert distance(board, (6, 6), (0, 0)) == UNREACHABLE


def test_barrier_cells_are_never_reachable() -> None:
    board = Board(7, [(3, 4)])
    assert distance_field(board, (3, 3))[(3, 4)] == UNREACHABLE


def test_a_blocked_source_reaches_nothing() -> None:
    board = Board(7, [(3, 3)])
    field = distance_field(board, (3, 3))
    assert all(value == UNREACHABLE for value in field.values())


def test_step_toward_moves_along_a_shortest_path() -> None:
    board = Board(7)
    assert step_toward(board, (0, 0), (3, 0)) == "S"
    assert step_toward(board, (0, 0), (0, 3)) == "E"


def test_step_toward_breaks_ties_deterministically() -> None:
    """N-S-E-W order: both S and E shorten the path; S is listed first."""
    assert step_toward(Board(7), (0, 0), (3, 3)) == "S"


def test_step_toward_routes_around_a_wall() -> None:
    wall = [(0, 1), (1, 1), (2, 1)]
    board = Board(7, wall)
    assert step_toward(board, (0, 0), (0, 2)) == "S"


def test_step_toward_an_unreachable_target_stays_put() -> None:
    pocket_walls = [(0, 1), (1, 0), (1, 1)]
    board = Board(7, pocket_walls)
    assert step_toward(board, (6, 6), (0, 0)) == "STAY"


def test_step_toward_the_current_cell_stays_put() -> None:
    assert step_toward(Board(7), (3, 3), (3, 3)) == "STAY"


def test_step_away_flees_the_threat() -> None:
    board = Board(7)
    assert step_away(board, (3, 3), (0, 0)) == "S"


def test_step_away_stays_put_inside_a_sealed_refuge() -> None:
    """A region the threat cannot reach at all is already the safest place."""
    walls = [(0, 2), (1, 2), (1, 0), (1, 1)]
    board = Board(7, walls)
    assert step_away(board, (0, 1), (5, 5)) == "STAY"


def test_step_away_stays_put_when_every_step_helps_the_threat() -> None:
    walls = [(0, 1), (1, 0)]
    board = Board(7, walls)
    assert step_away(board, (0, 0), (5, 5)) == "STAY"


def test_the_field_covers_every_cell_of_the_board() -> None:
    board = Board(5)
    assert set(distance_field(board, (0, 0))) == set(board.cells())
