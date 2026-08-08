"""Fault containment for a networked series: one bad sub-game never zeroes the rest.

League series run between two students' laptops over public tunnels (ngrok,
Localtonet), so a mid-game silence, a timed-out turn, an equivocation, or an
unreadable reply is not exotic - it is Tuesday. Without containment a single
such hiccup propagates out of the sub-game and crashes the whole driver,
forfeiting every remaining sub-game with it. That is the worst outcome on the
board: the rulebook already scores an unfinished sub-game a technical loss
(nobody scores), but only if the series survives to play the next one.

This module names the failures that a sub-game may absorb locally and builds
the zeroed result row that stands in for the game that could not finish, so the
schedule always plays to its end.
"""

from __future__ import annotations

from typing import Any

from ..infra.mcp_client import PeerUnreachableError
from ..infra.transport import TransportError
from .turn_reorder import HandshakeRejectedError

#: Failures a sub-game absorbs as its own technical loss instead of crashing the
#: series. ``TimeoutError`` covers a stalled ``wait_for`` and the deadline
#: tracker's ``DeadlineExpiredError`` (its subclass); the RuntimeError family
#: covers an unreachable peer, a transport fault and a handshake refusal.
CONTAINED_FAILURES: tuple[type[Exception], ...] = (
    PeerUnreachableError,
    TransportError,
    HandshakeRejectedError,
    TimeoutError,
)


def failure_reason(error: BaseException) -> str:
    """A compact ``Type: message`` label for logs and the row's audit note."""
    return f"{type(error).__name__}: {error}"


def technical_loss_row(
    *,
    sub_game_number: int,
    us: str,
    opponent: str,
    role: str,
    expect_role: str,
    game_id: str,
    github_commit: str,
    reason: str,
) -> dict[str, Any]:
    """A properly-shaped zeroed result row for a sub-game that could not finish.

    Matches the shape the driver emits for a played sub-game so the result
    aggregate and the kit's checker read it without a special case. Nobody
    scores (rulebook technical loss); ``tampered`` stays false because a
    network failure is not a forgery, and ``log_verified`` is false because no
    disclosure was ever audited.
    """
    log_name = f"log_{game_id}_g{sub_game_number:02d}.json"
    return {
        "sub_game_number": sub_game_number,
        "roles": {us: role, opponent: expect_role},
        "started_at": "",
        "ended_at": "",
        "result": "technical_loss",
        "winner_group": None,
        "tie": False,
        "steps": 0,
        "github_commit": {us: github_commit, opponent: "unknown"},
        "tokens": {us: 0, opponent: 0},
        "score": {us: 0, opponent: 0},
        "log_files": {us: log_name, opponent: log_name},
        "audit": {"log_verified": False, "tampered": False, "reason": reason},
    }
