"""Command-line entry point.

This layer contains no game logic whatsoever: it parses arguments, calls the
SDK, and renders text. Every rule it appears to enforce is enforced inside the
domain layer.

Usage::

    uv run python -m police_thief demo                # local mini-game
    uv run python -m police_thief peer --role police   # serve + reach the opponent
    uv run python -m police_thief replay --log <file>  # verified match replay
"""

from __future__ import annotations

import argparse
import sys

from .constants import ROLE_POLICE
from .domain.state import GameState
from .sdk import SimulationSdk
from .services.runtime import runner_from_config
from .shared.config import ConfigManager

_CELL_EMPTY = "."
_CELL_BARRIER = "#"
_CELL_COP = "C"
_CELL_THIEF = "T"
_CELL_BOTH = "X"


def render(state: GameState) -> str:
    """Draw the objective board as text, for local development only.

    The live GUI shows *local truth* only; this developer view is deliberately
    kept out of the agent's own interface.
    """
    rows = []
    for row in range(state.board.size):
        cells = []
        for col in range(state.board.size):
            cells.append(_glyph(state, (row, col)))
        rows.append(" ".join(cells))
    return "\n".join(rows)


def _glyph(state: GameState, cell: tuple[int, int]) -> str:
    """The single character representing one cell."""
    if cell == state.cop and cell == state.thief:
        return _CELL_BOTH
    if cell == state.cop:
        return _CELL_COP
    if cell == state.thief:
        return _CELL_THIEF
    if state.board.is_barrier(cell):
        return _CELL_BARRIER
    return _CELL_EMPTY


def run_demo(quiet: bool = False) -> int:
    """Play one mini-game between the configured brains and report the result."""
    config = ConfigManager.load(ROLE_POLICE)
    sdk = SimulationSdk(config)
    runner = runner_from_config(config)
    if not quiet:
        print(f"board {sdk.contract.board.grid_size}x{sdk.contract.board.grid_size}, "
              f"contract {sdk.config_sha256[:12]}")
    state = runner.play()
    if not quiet:
        print(render(state), end="\n\n")
    outcome = state.outcome
    if outcome is None:  # pragma: no cover - play() only returns when finished
        return 1
    print(f"{outcome.event}: {outcome.reason}")
    print(f"steps {state.step} | cop {outcome.cop_points} | thief {outcome.thief_points}")
    return 0


def run_peer(role: str, peer_id: str, games_played: int,
             wait: float | None = None, linger: float | None = None) -> int:
    """Boot one peer process and probe connectivity to its opponent.

    The two peers are started by hand in two terminals, so whichever goes first
    waits (up to ``wait``) for the other rather than declaring it unreachable,
    then lingers (``linger``) so the slower side's own probe lands before we go.
    """
    from .services.peer_boot import (
        DEFAULT_LINGER_SECONDS,
        DEFAULT_WAIT_SECONDS,
        check_connectivity,
    )

    wait = DEFAULT_WAIT_SECONDS if wait is None else wait
    linger = DEFAULT_LINGER_SECONDS if linger is None else linger
    print(f"[{role}] serving; waiting up to {wait:.0f}s for the opponent")
    report = check_connectivity(
        ConfigManager.load(role), peer_id, games_played,
        wait_seconds=wait, linger_seconds=linger,
        announce=lambda message: print(f"[{role}] {message}"),
    )
    status = "OK" if report.handshake_ok else "FAILED"
    print(f"[{report.role}] serving on port {report.my_port}")
    print(f"[{report.role}] opponent at {report.opponent_url}")
    print(f"[{report.role}] handshake {status}: {report.detail}")
    return 0 if report.handshake_ok else 1


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and dispatch to a sub-command."""
    parser = argparse.ArgumentParser(prog="police_thief", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    demo = sub.add_parser("demo", help="play a scripted local mini-game")
    demo.add_argument("--quiet", action="store_true", help="print only the result")
    peer = sub.add_parser("peer", help="boot a peer process and reach the opponent")
    peer.add_argument("--role", required=True, choices=["police", "thief"])
    peer.add_argument("--peer-id", default="team-dev")
    peer.add_argument("--games-played", type=int, default=0)
    # Defaults resolve inside run_peer: peer_boot pulls in the MCP stack, and the
    # CLI must stay importable (and `demo`/`replay` usable) without paying for it.
    peer.add_argument("--wait", type=float, default=None,
                      help="seconds to wait for an opponent that has not started yet")
    peer.add_argument("--linger", type=float, default=None,
                      help="seconds to keep serving after our handshake lands")
    replay = sub.add_parser("replay", help="open the verified replay viewer")
    replay.add_argument("--log", required=True, help="path of a saved log_<id>_gNN.json")
    args = parser.parse_args(argv)
    if args.command == "demo":
        return run_demo(quiet=args.quiet)
    if args.command == "peer":
        return run_peer(args.role, args.peer_id, args.games_played, args.wait, args.linger)
    if args.command == "replay":  # pragma: no cover - requires a display
        from .gui.replay import ReplayWindow

        ReplayWindow(args.log).run()
        return 0
    return 1  # pragma: no cover - argparse rejects unknown commands


if __name__ == "__main__":
    sys.exit(main())
