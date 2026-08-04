"""Tests for point allocation across every termination scenario."""

from __future__ import annotations

import pytest

from police_thief.domain.scoring import (
    Outcome,
    capture,
    series_totals,
    survival,
    technical_loss,
    tie,
)
from police_thief.shared.schema import ScoringConfig

SCORING = ScoringConfig(
    capture_cop=20,
    capture_thief=5,
    survival_cop=5,
    survival_thief=10,
    tie_score=2,
    technical_loss=0,
)


def test_capture_pays_the_cop_his_highest_reward() -> None:
    outcome = capture(SCORING)
    assert (outcome.cop_points, outcome.thief_points) == (20, 5)
    assert outcome.event == "capture"


def test_survival_pays_the_thief_his_highest_reward() -> None:
    outcome = survival(SCORING)
    assert (outcome.cop_points, outcome.thief_points) == (5, 10)
    assert outcome.event == "survival"


def test_a_technical_loss_zeroes_both_sides() -> None:
    """Neither peer may gain by breaking the protocol."""
    outcome = technical_loss(SCORING, "opponent missed the deadline")
    assert (outcome.cop_points, outcome.thief_points) == (0, 0)
    assert outcome.reason == "opponent missed the deadline"


def test_a_tie_pays_both_sides_the_tie_score() -> None:
    outcome = tie(SCORING)
    assert (outcome.cop_points, outcome.thief_points) == (2, 2)


def test_the_capture_reward_beats_the_survival_reward_for_the_cop() -> None:
    assert capture(SCORING).cop_points > survival(SCORING).cop_points


def test_the_survival_reward_beats_the_capture_reward_for_the_thief() -> None:
    assert survival(SCORING).thief_points > capture(SCORING).thief_points


def test_points_for_resolves_by_role() -> None:
    outcome = capture(SCORING)
    assert outcome.points_for("police") == 20
    assert outcome.points_for("thief") == 5


def test_points_for_rejects_an_unknown_role() -> None:
    with pytest.raises(ValueError, match="unknown role"):
        capture(SCORING).points_for("burglar")


def test_a_custom_reason_is_carried_through() -> None:
    outcome = capture(SCORING, "a barrier was placed on the thief's cell")
    assert "barrier" in outcome.reason


def test_series_totals_sum_every_mini_game() -> None:
    outcomes = [capture(SCORING), survival(SCORING), technical_loss(SCORING, "crash")]
    assert series_totals(outcomes) == (25, 15)


def test_series_totals_of_an_empty_series_are_zero() -> None:
    assert series_totals([]) == (0, 0)


def test_an_outcome_is_immutable() -> None:
    """A recorded result must not be editable after the fact."""
    outcome = capture(SCORING)
    with pytest.raises(AttributeError):
        outcome.cop_points = 99  # type: ignore[misc]


def test_outcome_can_be_constructed_directly() -> None:
    outcome = Outcome(event="capture", cop_points=20, thief_points=5, reason="test")
    assert outcome.points_for("police") == 20
