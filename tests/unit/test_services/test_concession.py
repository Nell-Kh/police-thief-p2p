"""Tests for the concession protocol - how a trapped thief's loss crosses the wire.

Found by the region cop: the first strategy that ever converted a networked
capture exposed a dead end in the ending flow - the thief detected its own
loss and went silent, so the winner never learned it won. The concession
message closes that hole; these tests pin every side of it.
"""

from __future__ import annotations

import pytest

from police_thief.domain.crypto import verify
from police_thief.domain.turnmsg import TurnMessage
from police_thief.services.match_runtime import MatchRuntime
from police_thief.services.turn_receiving import receive_turn
from police_thief.services.world_view import WorldView
from police_thief.shared.config import ConfigManager


@pytest.fixture(scope="module")
def config_police() -> ConfigManager:
    return ConfigManager.load("police")


@pytest.fixture(scope="module")
def config_thief() -> ConfigManager:
    return ConfigManager.load("thief")


def message(sender: str, **extra) -> TurnMessage:
    """A minimal legal turn message from ``sender``."""
    return TurnMessage(
        step=extra.pop("step", 5), sender=sender, hint="", smell_grid={},
        commit="a" * 64, **extra,
    )


def test_a_trapping_barrier_makes_the_thief_concede(config_thief: ConfigManager) -> None:
    runtime = MatchRuntime(config_thief, game_id="c1", sub_game=1, github_commit="x")
    trap = message("police", barrier_placed=list(runtime.view.position))
    reply = runtime.on_turn(trap)
    assert runtime.result == {"type": "capture", "winner": "police", "how": "trapping barrier"}
    assert reply is not None and reply.win_claim == {"type": "capture", "winner": "police"}
    assert reply.sender == "thief"


def test_the_concession_is_sealed_into_the_logbook(config_thief: ConfigManager) -> None:
    runtime = MatchRuntime(config_thief, game_id="c2", sub_game=1, github_commit="x")
    reply = runtime.on_turn(message("police", barrier_placed=list(runtime.view.position)))
    record = runtime.book.records[-1]
    assert record["payload"]["type"] == "concession"
    assert record["commit"] == reply.commit
    assert verify(record["payload"], record["nonce"], record["commit"])


def test_the_thief_concedes_exactly_once(config_thief: ConfigManager) -> None:
    runtime = MatchRuntime(config_thief, game_id="c3", sub_game=1, github_commit="x")
    first = runtime.on_turn(message("police", barrier_placed=list(runtime.view.position)))
    second = runtime.on_turn(message("police", step=6))
    assert first is not None and second is None


def test_the_police_accepts_the_concession(config_police: ConfigManager) -> None:
    runtime = MatchRuntime(config_police, game_id="c4", sub_game=1, github_commit="x")
    reply = runtime.on_turn(message("thief", win_claim={"type": "capture"}))
    assert runtime.result == {"type": "capture", "winner": "police", "how": "conceded"}
    assert reply is None  # only the thief ever concedes


def test_a_concession_from_the_police_side_is_ignored(config_thief: ConfigManager) -> None:
    """A malicious cop cannot win by 'conceding' on the thief's behalf."""
    view = WorldView.open("thief", config_thief.contract)
    receive_turn(view, message("police", win_claim={"type": "capture"}), config_thief.contract)
    assert view.result is None


def test_a_survival_claim_from_the_police_side_is_ignored(
    config_police: ConfigManager,
) -> None:
    """Only the thief may claim survival - and never below the threshold."""
    view = WorldView.open("police", config_police.contract)
    receive_turn(
        view, message("police", step=40, win_claim={"type": "survival"}),
        config_police.contract,
    )
    assert view.result is None
