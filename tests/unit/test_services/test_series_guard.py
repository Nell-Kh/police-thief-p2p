"""Tests for series fault containment - a bad sub-game must not zero the series."""

from __future__ import annotations

import pytest

from police_thief.infra.mcp_client import PeerUnreachableError
from police_thief.infra.transport import TransportError
from police_thief.services.deadline import DeadlineExpiredError
from police_thief.services.series_guard import (
    CONTAINED_FAILURES,
    failure_reason,
    technical_loss_row,
)
from police_thief.services.turn_reorder import HandshakeRejectedError


@pytest.mark.parametrize(
    "error",
    [
        PeerUnreachableError("opponent silent"),
        TransportError("connection reset"),
        HandshakeRejectedError("equivocated commit"),
        TimeoutError("no turn arrived"),
        DeadlineExpiredError("reply too late"),  # a TimeoutError subclass
    ],
)
def test_every_live_failure_is_contained(error: Exception) -> None:
    """The exact exceptions a flaky tunnel throws are all caught by the tuple."""
    try:
        raise error
    except CONTAINED_FAILURES as caught:
        assert caught is error
    else:  # pragma: no cover - the raise above always fires
        pytest.fail(f"{type(error).__name__} escaped containment")


def test_a_programming_bug_is_not_swallowed() -> None:
    """Containment is for network faults, not for masking our own KeyError."""
    with pytest.raises(KeyError):
        try:
            raise KeyError("a real bug")
        except CONTAINED_FAILURES:  # pragma: no cover - must not catch
            pytest.fail("containment swallowed a programming error")


def test_the_technical_loss_row_is_shaped_like_a_played_row() -> None:
    row = technical_loss_row(
        sub_game_number=3, us="yanell11", opponent="rivals", role="police",
        expect_role="thief", game_id="yanell11-vs-rivals", github_commit="abc123",
        reason="PeerUnreachableError: opponent silent",
    )
    assert row["result"] == "technical_loss"
    assert row["score"] == {"yanell11": 0, "rivals": 0}  # nobody scores
    assert row["winner_group"] is None and row["tie"] is False
    assert row["roles"] == {"yanell11": "police", "rivals": "thief"}  # complementary
    assert row["github_commit"] == {"yanell11": "abc123", "rivals": "unknown"}
    assert row["log_files"]["yanell11"] == "log_yanell11-vs-rivals_g03.json"
    assert row["audit"] == {"log_verified": False, "tampered": False,
                            "reason": "PeerUnreachableError: opponent silent"}


def test_a_contained_failure_is_never_scored_as_tampering() -> None:
    """A silent opponent is a technical loss, not a forgery - keep them distinct."""
    row = technical_loss_row(
        sub_game_number=1, us="a", opponent="b", role="thief", expect_role="police",
        game_id="a-vs-b", github_commit="x", reason="timeout",
    )
    assert row["audit"]["tampered"] is False  # not a tamper_forfeit


def test_failure_reason_is_a_compact_type_and_message() -> None:
    assert failure_reason(PeerUnreachableError("gone")) == "PeerUnreachableError: gone"
