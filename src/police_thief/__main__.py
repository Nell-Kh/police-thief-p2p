"""Command-line entry point.

This layer contains no game logic whatsoever: it parses arguments, calls the
SDK, and renders text. Every rule it appears to enforce is enforced inside the
domain layer.

Usage::

    uv run python -m police_thief demo          # scripted local mini-game
    uv run python -m police_thief demo --quiet  # result only
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


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and dispatch to a sub-command."""
    parser = argparse.ArgumentParser(prog="police_thief", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    demo = sub.add_parser("demo", help="play a scripted local mini-game")
    demo.add_argument("--quiet", action="store_true", help="print only the result")
    args = parser.parse_args(argv)
    if args.command == "demo":
        return run_demo(quiet=args.quiet)
    return 1  # pragma: no cover - argparse rejects unknown commands


if __name__ == "__main__":
    sys.exit(main())
