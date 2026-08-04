"""Tests for the movement and barrier laws."""

from __future__ import annotations

import pytest

from police_thief.domain.board import Board
from police_thief.domain.rules import (
    IllegalBarrierError,
    IllegalMoveError,
    barrier_placements,
    destination,
    is_legal_move,
    is_trapped,
    legal_moves,
    legal_steps,
    validate_barrier,
    validate_move,
)


def test_destination_applies_the_four_directions() -> None:
    assert destination((3, 3), "N") == (2, 3)
    assert destination((3, 3), "S") == (4, 3)
    assert destination((3, 3), "E") == (3, 4)
    assert destination((3, 3), "W") == (3, 2)


def test_staying_keeps_the_agent_in_place() -> None:
    assert destination((3, 3), "STAY") == (3, 3)


@pytest.mark.parametrize("move", ["NE", "SW", "diagonal", "", "n"])
def test_a_diagonal_or_unknown_move_is_rejected(move: str) -> None:
    """Diagonals are unrepresentable, so they surface as unknown moves."""
    with pytest.raises(IllegalMoveError, match="unknown move"):
        destination((3, 3), move)


def test_a_move_off_the_board_is_illegal() -> None:
    assert not is_legal_move(Board(7), (0, 0), "N")


def test_a_move_into_a_barrier_is_illegal() -> None:
    assert not is_legal_move(Board(7, [(2, 3)]), (3, 3), "N")


def test_an_unknown_move_is_never_legal() -> None:
    assert not is_legal_move(Board(7), (3, 3), "NE")


def test_legal_moves_in_the_open_are_all_five() -> None:
    assert set(legal_moves(Board(7), (3, 3))) == {"N", "S", "E", "W", "STAY"}


def test_legal_moves_in_a_corner_drop_the_off_board_directions() -> None:
    assert set(legal_moves(Board(7), (0, 0))) == {"S", "E", "STAY"}


def test_legal_moves_are_returned_in_deterministic_order() -> None:
    """Both peers must break ties identically to stay reproducible."""
    assert legal_moves(Board(7), (3, 3)) == ["N", "S", "E", "W", "STAY"]


def test_legal_steps_exclude_staying() -> None:
    assert "STAY" not in legal_steps(Board(7), (3, 3))


def test_validate_move_returns_the_destination() -> None:
    assert validate_move(Board(7), (3, 3), "N") == (2, 3)


def test_validate_move_rejects_leaving_the_board() -> None:
    with pytest.raises(IllegalMoveError, match="leaves the board"):
        validate_move(Board(7), (0, 0), "N")


def test_validate_move_rejects_entering_a_barrier() -> None:
    with pytest.raises(IllegalMoveError, match="enters barrier"):
        validate_move(Board(7, [(2, 3)]), (3, 3), "N")


def test_an_agent_in_the_open_is_not_trapped() -> None:
    assert not is_trapped(Board(7), (3, 3))


def test_an_agent_walled_in_on_all_four_sides_is_trapped() -> None:
    board = Board(7, [(2, 3), (4, 3), (3, 2), (3, 4)])
    assert is_trapped(board, (3, 3))


def test_a_corner_agent_is_trapped_by_two_barriers() -> None:
    """The board edge counts as a wall for trapping purposes."""
    assert is_trapped(Board(7, [(0, 1), (1, 0)]), (0, 0))


def test_staying_does_not_rescue_a_trapped_agent() -> None:
    board = Board(7, [(0, 1), (1, 0)])
    assert "STAY" in legal_moves(board, (0, 0))
    assert is_trapped(board, (0, 0))


def test_barrier_placements_cover_the_cop_cell_and_its_neighbours() -> None:
    assert sorted(barrier_placements(Board(7), (3, 3))) == [
        (2, 3),
        (3, 2),
        (3, 3),
        (3, 4),
        (4, 3),
    ]


def test_barrier_placements_exclude_cells_already_blocked() -> None:
    board = Board(7, [(2, 3)])
    assert (2, 3) not in barrier_placements(board, (3, 3))


def test_barrier_placements_stay_on_the_board() -> None:
    assert sorted(barrier_placements(Board(7), (0, 0))) == [(0, 0), (0, 1), (1, 0)]


def test_a_barrier_requires_forgoing_movement() -> None:
    with pytest.raises(IllegalBarrierError, match="without movement"):
        validate_barrier(Board(7), (3, 3), (3, 4), move="E", used=0, quota=14)


def test_a_barrier_beyond_the_quota_is_rejected() -> None:
    with pytest.raises(IllegalBarrierError, match="quota exhausted"):
        validate_barrier(Board(7), (3, 3), (3, 4), move="STAY", used=14, quota=14)


def test_a_barrier_out_of_reach_is_rejected() -> None:
    with pytest.raises(IllegalBarrierError, match="within one step"):
        validate_barrier(Board(7), (3, 3), (6, 6), move="STAY", used=0, quota=14)


def test_a_barrier_on_an_occupied_barrier_cell_is_rejected() -> None:
    board = Board(7, [(3, 4)])
    with pytest.raises(IllegalBarrierError, match="within one step"):
        validate_barrier(board, (3, 3), (3, 4), move="STAY", used=0, quota=14)


def test_a_lawful_barrier_passes_validation() -> None:
    validate_barrier(Board(7), (3, 3), (3, 4), move="STAY", used=0, quota=14)
