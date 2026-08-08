"""Shared machinery for the networked series drivers.

Both :mod:`friendly_series` (any real opponent) and :mod:`sparring_series` (the
class interop kit's sparring peer) drive the same protocol: serve one long-lived
FastMCP server, swap in a fresh :class:`InboundHandler` at every sub-game
boundary as the role alternates, alternate real ``receive_turn`` calls with the
opponent, then exchange audit disclosures. That machinery lives here once so the
two drivers differ only in the parts that are genuinely different - who the
opponent is, and which artifacts get written.
"""

from __future__ import annotations

import subprocess
import sys
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from police_thief.constants import ROLE_POLICE, ROLE_THIEF  # noqa: E402
from police_thief.infra.mcp_server import build_server  # noqa: E402
from police_thief.services.inbound import InboundHandler  # noqa: E402
from police_thief.services.match_runtime import MatchRuntime  # noqa: E402

#: Hard stop on a sub-game's turn exchange, so a wedged peer can never hang us.
SAFETY_CAP = 200
TURN_WAIT_TIMEOUT = 60.0
NEGOTIATE_WAIT_TIMEOUT = 180.0
POLL_INTERVAL = 0.2


def other_role(role: str) -> str:
    """The role the opponent plays when we play ``role``."""
    return ROLE_THIEF if role == ROLE_POLICE else ROLE_POLICE


def git_head() -> str:
    """This working tree's HEAD commit, or ``"uncommitted"`` when unavailable."""
    out = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                         check=False, cwd=ROOT)
    return out.stdout.strip() or "uncommitted"


class SwappableHandler:
    """Holds the :class:`InboundHandler` currently active; the tools delegate to it.

    One process serves every sub-game's worth of negotiate/receive_turn/
    submit_audit/receive_control calls; the *object* backing those calls is
    replaced at each sub-game boundary, exactly as the kit's own driver swaps in
    a fresh peer. Duck-types the four methods :func:`build_server` binds.
    """

    def __init__(self) -> None:
        """Start with no handler bound; the first sub-game installs one."""
        self.current: InboundHandler | None = None

    def negotiate(self, message: dict[str, Any]) -> dict[str, Any]:
        """Forward a handshake to the active handler."""
        return self.current.negotiate(message)

    def receive_turn(self, message: dict[str, Any]) -> dict[str, Any]:
        """Forward a turn to the active handler."""
        return self.current.receive_turn(message)

    def submit_audit(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Forward an audit disclosure to the active handler."""
        return self.current.submit_audit(payload)

    def receive_control(self, message: dict[str, Any]) -> dict[str, Any]:
        """Forward a control message to the active handler."""
        return self.current.receive_control(message)


def start_server(handler_box: SwappableHandler, port: int,
                 host: str = "127.0.0.1") -> threading.Thread:
    """Run our MCP server in a daemon thread on ``host:port``.

    ``127.0.0.1`` is right when a tunnel agent runs on this machine (it dials
    localhost itself); pass ``0.0.0.0`` to accept a direct remote connection.
    """
    server = build_server(handler_box)
    thread = threading.Thread(
        target=lambda: server.run(transport="http", host=host, port=port, show_banner=False),
        daemon=True,
    )
    thread.start()
    return thread


def wait_for(predicate: Callable[[], Any], timeout: float, what: str) -> Any:
    """Poll ``predicate`` until it returns non-None, or raise ``TimeoutError``."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = predicate()
        if value is not None:
            return value
        time.sleep(POLL_INTERVAL)
    raise TimeoutError(f"timed out after {timeout}s waiting for {what}")


def play_networked(role: str, matchrt: MatchRuntime, client, handler: InboundHandler) -> None:
    """Alternate turns with a real remote opponent - the thief always moves first."""
    thief_is_us = role == ROLE_THIEF
    for _ in range(SAFETY_CAP):
        if matchrt.ended:
            return
        if thief_is_us:
            client.send_turn(matchrt.play_turn().to_wire())
            if matchrt.ended:
                return
        incoming = wait_for(handler.next_turn, TURN_WAIT_TIMEOUT,
                            f"opponent's turn (sub-game {matchrt.book.sub_game}, "
                            f"step {handler.next_step})")
        reply = matchrt.on_turn(incoming)
        if reply is not None:
            client.send_turn(reply.to_wire())
        if matchrt.ended:
            return
        if not thief_is_us:
            client.send_turn(matchrt.play_turn().to_wire())
    raise RuntimeError(f"sub-game {matchrt.book.sub_game}: safety cap ({SAFETY_CAP}) exceeded")


def score_for(contract, outcome_type: str, role: str) -> int:
    """Points ``role`` earns for ``outcome_type`` under the contract's table."""
    scoring = contract.scoring
    if outcome_type == "capture":
        return scoring.capture_cop if role == ROLE_POLICE else scoring.capture_thief
    if outcome_type == "survival":
        return scoring.survival_thief if role == ROLE_THIEF else scoring.survival_cop
    return scoring.technical_loss
