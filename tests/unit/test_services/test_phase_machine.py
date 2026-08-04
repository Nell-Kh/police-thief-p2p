"""Tests for the turn state machine."""

from __future__ import annotations

import pytest

from police_thief.services.phase_machine import GamePhaseMachine, IllegalTransitionError


def test_the_machine_starts_waiting_for_the_opponent() -> None:
    assert GamePhaseMachine().state == "WAITING_FOR_OPPONENT"


def test_an_unknown_starting_phase_is_rejected() -> None:
    with pytest.raises(IllegalTransitionError, match="unknown phase"):
        GamePhaseMachine("DAYDREAMING")


def test_a_full_turn_walks_the_legal_cycle() -> None:
    machine = GamePhaseMachine()
    for phase in ["COMPUTING_MOVE", "COMMITTING", "AWAITING_REVEAL", "VERIFYING"]:
        machine.transition(phase)
    assert machine.transition("WAITING_FOR_OPPONENT") == "WAITING_FOR_OPPONENT"


def test_skipping_a_phase_is_refused() -> None:
    """Committing before computing would break the protocol's ordering."""
    machine = GamePhaseMachine()
    with pytest.raises(IllegalTransitionError, match="illegal transition"):
        machine.transition("COMMITTING")


def test_transition_to_an_unknown_phase_is_refused() -> None:
    with pytest.raises(IllegalTransitionError, match="unknown phase"):
        GamePhaseMachine().transition("PANICKING")


def test_can_reports_legality_without_moving() -> None:
    machine = GamePhaseMachine()
    assert machine.can("COMPUTING_MOVE")
    assert not machine.can("VERIFYING")
    assert machine.state == "WAITING_FOR_OPPONENT"


def test_start_turn_is_a_shortcut_into_computing() -> None:
    assert GamePhaseMachine().start_turn() == "COMPUTING_MOVE"


def test_a_stalled_reveal_exits_to_technical_loss() -> None:
    """If the opponent disconnects mid-turn, we announce a result, not hang."""
    machine = GamePhaseMachine()
    machine.start_turn()
    machine.transition("COMMITTING")
    machine.transition("AWAITING_REVEAL")
    assert machine.fail() == "TECHNICAL_LOSS"


def test_failing_from_a_phase_without_an_exit_still_terminates() -> None:
    """A peer that cannot continue must announce a result from any phase."""
    machine = GamePhaseMachine()
    assert machine.fail() == "TECHNICAL_LOSS"


def test_technical_loss_is_terminal() -> None:
    machine = GamePhaseMachine()
    machine.fail()
    assert machine.terminal
    with pytest.raises(IllegalTransitionError):
        machine.transition("WAITING_FOR_OPPONENT")


def test_a_normal_phase_is_not_terminal() -> None:
    assert not GamePhaseMachine().terminal


def test_the_trail_records_every_phase_visited() -> None:
    machine = GamePhaseMachine()
    machine.start_turn()
    machine.transition("COMMITTING")
    assert machine.trail == ("WAITING_FOR_OPPONENT", "COMPUTING_MOVE", "COMMITTING")


def test_every_phase_is_reachable_from_the_start() -> None:
    """No phase in the table is dead code."""
    reachable = {"WAITING_FOR_OPPONENT"}
    frontier = list(reachable)
    while frontier:
        current = frontier.pop()
        for target in GamePhaseMachine.TRANSITIONS[current]:
            if target not in reachable:
                reachable.add(target)
                frontier.append(target)
    assert reachable == set(GamePhaseMachine.TRANSITIONS)


def test_repr_shows_the_current_phase() -> None:
    assert "WAITING_FOR_OPPONENT" in repr(GamePhaseMachine())
