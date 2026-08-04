"""Tests for the region cop - the notebook's discovery, pinned as physics."""

from __future__ import annotations

import pytest

from police_thief.constants import MOVE_STAY, ROLE_POLICE, ROLE_THIEF
from police_thief.domain.board import Board
from police_thief.domain.brain.base import BrainView
from police_thief.domain.brain.enhanced import EnhancedThiefBrain
from police_thief.domain.brain.region import RegionPoliceBrain, region_size
from police_thief.domain.state import GameState
from police_thief.sdk import SimulationSdk
from police_thief.services.runtime import LocalMatchRunner
from police_thief.shared.config import ConfigManager


@pytest.fixture(scope="module")
def config() -> ConfigManager:
    return ConfigManager.load(ROLE_POLICE)


@pytest.fixture
def cop(config: ConfigManager) -> RegionPoliceBrain:
    return RegionPoliceBrain(ROLE_POLICE, config.contract)


def view(board: Board, cop_at, thief_at, barriers_left: int = 10, step: int = 1) -> BrainView:
    return BrainView(
        role=ROLE_POLICE, position=cop_at, target=thief_at,
        board=board, barriers_left=barriers_left, step=step,
    )


def test_region_size_counts_cells_the_thief_reaches_first() -> None:
    board = Board(3)
    # Cop in one corner, thief in the other: the thief owns its near half.
    assert region_size(board, (0, 0), (2, 2)) == 3  # (2,2), (1,2), (2,1)
    assert region_size(board, (2, 2), (2, 2)) == 0  # overlap: nothing is safe


def test_region_size_respects_barriers() -> None:
    walled = Board(3, [(1, 2), (2, 1)])
    # The corner pocket (2,2) is sealed off: the thief inside keeps only it.
    assert region_size(walled, (0, 0), (2, 2)) == 1


def test_the_adjacent_trap_still_fires_first(cop: RegionPoliceBrain) -> None:
    board = Board(7)
    action = cop.decide(view(board, (5, 6), (6, 6)))
    assert action.move == MOVE_STAY
    assert action.barrier == (6, 6)


def test_midgame_barriers_below_min_shrink_are_refused(cop: RegionPoliceBrain) -> None:
    """On an open board no single early barrier starves 3 cells - so move."""
    board = Board(7)
    action = cop.decide(view(board, (0, 0), (6, 6)))
    assert action.barrier is None
    assert action.move != MOVE_STAY  # never donate a turn to the parity dance


def test_endgame_seals_the_cornered_thiefs_exit(cop: RegionPoliceBrain) -> None:
    """The position the pinch cop danced at forever: region 1, diagonal cop."""
    board = Board(7)
    action = cop.decide(view(board, (5, 5), (6, 6)))
    assert action.move == MOVE_STAY
    assert action.barrier in {(5, 6), (6, 5)}  # one corner exit sealed


def test_without_quota_the_cop_still_moves(cop: RegionPoliceBrain) -> None:
    board = Board(7)
    action = cop.decide(view(board, (5, 5), (6, 6), barriers_left=0))
    assert action.barrier is None


def test_decisions_are_deterministic(cop: RegionPoliceBrain) -> None:
    board = Board(7)
    first = cop.decide(view(board, (3, 0), (3, 6)))
    assert all(cop.decide(view(board, (3, 0), (3, 6))) == first for _ in range(3))


@pytest.mark.parametrize("starts", [((0, 0), (6, 6)), ((3, 3), (0, 6)), ((6, 0), (0, 3))])
def test_the_region_cop_converts_where_the_pinch_cop_could_not(
    config: ConfigManager, starts
) -> None:
    """Full mini-games from the notebook's worst starts: all captures now."""
    runner = LocalMatchRunner(
        SimulationSdk(config),
        police_brain=RegionPoliceBrain(ROLE_POLICE, config.contract),
        thief_brain=EnhancedThiefBrain(ROLE_THIEF, config.contract),
    )
    state = GameState(board=Board(config.contract.board.grid_size), cop=starts[0],
                      thief=starts[1])
    while not state.finished:
        runner.play_turn(state)
    assert state.outcome is not None
    assert state.outcome.event == "capture"
    assert state.barriers_used <= 3  # conversion is cheap, quota stays banked
