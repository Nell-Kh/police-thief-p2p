"""Tests for the board geometry and barrier bookkeeping."""

from __future__ import annotations

import pytest

from police_thief.domain.board import Board, BoardError


def test_board_exposes_its_size() -> None:
    assert Board(7).size == 7


def test_board_rejects_a_non_positive_size() -> None:
    with pytest.raises(BoardError, match="must be positive"):
        Board(0)


def test_a_new_board_has_no_barriers() -> None:
    assert Board(7).barriers == frozenset()


def test_board_can_start_with_barriers() -> None:
    board = Board(7, [(1, 1), (2, 2)])
    assert board.barriers == frozenset({(1, 1), (2, 2)})


def test_in_bounds_accepts_every_corner() -> None:
    board = Board(7)
    for cell in [(0, 0), (0, 6), (6, 0), (6, 6)]:
        assert board.in_bounds(cell)


@pytest.mark.parametrize("cell", [(-1, 0), (0, -1), (7, 0), (0, 7)])
def test_in_bounds_rejects_cells_outside_the_grid(cell) -> None:
    assert not Board(7).in_bounds(cell)


def test_placing_a_barrier_blocks_the_cell() -> None:
    board = Board(7)
    board.place_barrier((3, 3))
    assert board.is_barrier((3, 3))
    assert not board.is_free((3, 3))


def test_barriers_are_irreversible_so_a_repeat_is_rejected() -> None:
    board = Board(7)
    board.place_barrier((3, 3))
    with pytest.raises(BoardError, match="already placed"):
        board.place_barrier((3, 3))


def test_a_barrier_outside_the_board_is_rejected() -> None:
    with pytest.raises(BoardError, match="outside a 7x7 board"):
        Board(7).place_barrier((7, 7))


def test_a_free_cell_is_on_board_and_unblocked() -> None:
    board = Board(7, [(1, 1)])
    assert board.is_free((0, 0))
    assert not board.is_free((1, 1))
    assert not board.is_free((9, 9))


def test_occupancy_does_not_block_a_cell() -> None:
    """An agent may step onto the opponent's cell - that overlap is a capture."""
    board = Board(7)
    assert board.is_free((3, 3))


def test_a_central_cell_has_four_neighbours() -> None:
    assert sorted(Board(7).neighbours((3, 3))) == [(2, 3), (3, 2), (3, 4), (4, 3)]


def test_a_corner_cell_has_two_neighbours() -> None:
    assert sorted(Board(7).neighbours((0, 0))) == [(0, 1), (1, 0)]


def test_no_neighbour_is_diagonal() -> None:
    for neighbour in Board(7).neighbours((3, 3)):
        row_gap = abs(neighbour[0] - 3)
        col_gap = abs(neighbour[1] - 3)
        assert row_gap + col_gap == 1


def test_free_neighbours_exclude_barriers() -> None:
    board = Board(7, [(2, 3)])
    assert sorted(board.free_neighbours((3, 3))) == [(3, 2), (3, 4), (4, 3)]


def test_cells_enumerates_the_whole_grid() -> None:
    cells = list(Board(7).cells())
    assert len(cells) == 49
    assert len(set(cells)) == 49


def test_copy_is_independent_of_the_original() -> None:
    """Look-ahead search must not be able to mutate the real board."""
    board = Board(7)
    clone = board.copy()
    clone.place_barrier((1, 1))
    assert not board.is_barrier((1, 1))
    assert clone.is_barrier((1, 1))


def test_repr_summarises_size_and_barrier_count() -> None:
    assert repr(Board(7, [(1, 1)])) == "Board(size=7, barriers=1)"
