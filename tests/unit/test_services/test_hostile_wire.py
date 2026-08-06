"""Fuzzing our own wire: hostile and buggy opponents must never crash us.

In a refereeless league, an opponent's garbage is a scoring event: caught, it
voids the game as their protocol violation; uncaught, it crashes us and the
watchdog charges US the technical loss. Every test here throws a class of
hostile input at the real receive path and asserts two invariants: no
exception escapes, and the verdict lands on the right side.
"""

from __future__ import annotations

import pytest

from police_thief.domain.turnmsg import TurnMessage, TurnMessageError
from police_thief.services.match_runtime import MatchRuntime
from police_thief.services.turn_receiving import receive_turn
from police_thief.services.world_view import WorldView
from police_thief.shared.config import ConfigManager


@pytest.fixture(scope="module")
def config() -> ConfigManager:
    return ConfigManager.load("thief")


@pytest.fixture
def view(config: ConfigManager) -> WorldView:
    return WorldView.open("thief", config.contract)


def msg(step: int = 1, sender: str = "police", **extra) -> TurnMessage:
    commit_val = extra.pop("commit", "a" * 64)
    return TurnMessage(step=step, sender=sender, hint="", smell_grid=extra.pop("smell", {}),
                       commit=commit_val, **extra)


def assert_violation(view: WorldView, config: ConfigManager, message: TurnMessage) -> None:
    receive_turn(view, message, config.contract)
    assert view.result is not None
    assert view.result["type"] == "technical_loss"
    assert view.result["violator"] == message.sender


# --- malformed wire payloads are refused at the parser ----------------------


@pytest.mark.parametrize("payload", [
    {"step": "abc", "sender": "police", "hint": "", "smell_grid": {}, "commit": "x"},
    {"step": 1, "sender": "police", "hint": "", "smell_grid": {}, "commit": "x",
     "barrier_placed": ["a", "b"]},
    {"step": 1, "sender": "police", "hint": "", "smell_grid": {}, "commit": "x",
     "capture_claim": [1, 2, 3]},
    {"step": 1, "sender": "police", "hint": "", "smell_grid": {"nonsense": "x"}, "commit": "x"},
    {"step": 1, "sender": "hacker", "hint": "", "smell_grid": {}, "commit": "x"},
    {"step": 1, "sender": "police", "hint": "", "smell_grid": {}, "commit": "x",
     "position": [3, 3]},  # cleartext position - the cardinal sin
])
def test_garbage_payloads_raise_the_controlled_error(payload: dict) -> None:
    with pytest.raises(TurnMessageError):
        TurnMessage.from_wire(payload)


# --- step forgery -----------------------------------------------------------


def test_an_opening_survival_jump_is_a_violation(view, config) -> None:
    """The classic forgery: open at step 35 and claim survival immediately."""
    assert_violation(view, config, msg(step=35, win_claim={"type": "survival"}))


def test_a_skipped_step_is_a_violation(view, config) -> None:
    receive_turn(view, msg(step=1), config.contract)
    assert_violation(view, config, msg(step=3))


def test_a_replayed_step_without_a_win_claim_is_a_violation(view, config) -> None:
    receive_turn(view, msg(step=1, commit="c1"), config.contract)
    assert_violation(view, config, msg(step=1, commit="c2"))


def test_the_concession_replay_exception_is_honoured(config) -> None:
    """A concession legally re-announces the current step (police side)."""
    police = WorldView.open("police", config.contract)
    receive_turn(police, msg(step=1, sender="thief", commit="c1"), config.contract)
    receive_turn(police, msg(step=1, sender="thief", claim_response={"claim": [0, 0], "caught": True}, commit="c2"),
                 config.contract)
    assert police.result == {"type": "capture", "winner": "police", "how": "capture claim"}


# --- scent physics forgery --------------------------------------------------


@pytest.mark.parametrize("smell", [
    {"3,3": float("nan")},
    {"3,3": float("inf")},
    {"3,3": -0.5},
    {"3,3": 5.0},          # above the locked emission ceiling
    {"99,0": 0.5},         # off the board - would drag the trust centroid
])
def test_forged_scent_fields_are_violations(view, config, smell) -> None:
    assert_violation(view, config, msg(smell=smell))


def test_lawful_scent_passes(view, config) -> None:
    receive_turn(view, msg(smell={"3,3": 0.9, "3,4": 0.62}), config.contract)
    assert view.result is None


# --- barrier law ------------------------------------------------------------


def test_a_thief_placing_a_barrier_is_a_violation(config) -> None:
    police = WorldView.open("police", config.contract)
    receive_turn(police, msg(sender="thief", barrier_placed=[2, 2]), config.contract)
    assert police.result["type"] == "technical_loss"


def test_an_off_board_barrier_is_a_violation(view, config) -> None:
    assert_violation(view, config, msg(barrier_placed=[9, 9]))


def test_the_barrier_quota_is_enforced_on_the_opponent(view, config) -> None:
    quota = config.contract.movement.max_barriers
    cells = [(r, c) for r in (0, 1) for c in range(7)] + [(5, 0), (5, 1)]
    step = 0
    for step, cell in enumerate(cells[:quota], start=1):
        receive_turn(view, msg(step=step, barrier_placed=list(cell)), config.contract)
        assert view.result is None
    assert view.opponent_barriers == quota
    receive_turn(view, msg(step=step + 1, barrier_placed=[6, 6]), config.contract)
    assert view.result["type"] == "technical_loss"
    assert "quota" in view.result["how"]


# --- claim permissions ------------------------------------------------------


def test_a_thief_making_capture_claims_is_a_violation(config) -> None:
    police = WorldView.open("police", config.contract)
    receive_turn(police, msg(sender="thief", capture_claim=[1, 1]), config.contract)
    assert police.result["type"] == "technical_loss"


def test_a_police_answering_claims_is_a_violation(view, config) -> None:
    assert_violation(view, config, msg(claim_response={"claim": [1, 1], "caught": False}))


def test_a_malformed_win_claim_is_a_violation(view, config) -> None:
    assert_violation(view, config, msg(win_claim="i win"))


# --- the whole runtime survives a hostile barrage ---------------------------


def test_the_runtime_never_crashes_on_a_hostile_barrage(config) -> None:
    """Every hostile message class, fired at a live runtime, in sequence."""
    runtime = MatchRuntime(config, game_id="fuzz", sub_game=1, github_commit="x")
    barrage = [
        msg(step=7),
        msg(step=1, smell={"3,3": float("nan")}),
        msg(step=1, barrier_placed=[-1, 0]),
        msg(step=1, sender="police", claim_response={"x": 1}),
        msg(step=35, win_claim={"type": "survival"}),
    ]
    for message in barrage:
        runtime.on_turn(message)  # must not raise
    assert runtime.result is not None
    assert runtime.result["type"] == "technical_loss"
