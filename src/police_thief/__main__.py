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

from .constants import ROLE_POLICE, ROLE_THIEF
from .domain.state import GameState
from .sdk import SimulationSdk

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


def _chase_move(sdk: SimulationSdk, state: GameState) -> str:
    """A placeholder cop policy: close the gap on one axis at a time.

    The real decision logic lives in the strategy module (phase 3); this exists
    only so the demo produces a complete game.
    """
    cop_row, cop_col = state.cop
    thief_row, thief_col = state.thief
    legal = sdk.legal_moves(state, ROLE_POLICE)
    if cop_row != thief_row:
        wanted = "S" if thief_row > cop_row else "N"
        if wanted in legal:
            return wanted
    if cop_col != thief_col:
        wanted = "E" if thief_col > cop_col else "W"
        if wanted in legal:
            return wanted
    return "STAY"


def run_demo(quiet: bool = False) -> int:
    """Play one scripted mini-game locally and report the result."""
    sdk = SimulationSdk.load(ROLE_POLICE)
    state = sdk.new_game()
    if not quiet:
        print(f"board {sdk.contract.board.grid_size}x{sdk.contract.board.grid_size}, "
              f"contract {sdk.config_sha256[:12]}")
        print(render(state), end="\n\n")
    while not state.finished:
        sdk.play_cop(state, _chase_move(sdk, state))
        if not state.finished:
            thief_moves = sdk.legal_moves(state, ROLE_THIEF)
            sdk.play_thief(state, thief_moves[0] if thief_moves else "STAY")
        sdk.end_turn(state)
    if not quiet:
        print(render(state), end="\n\n")
    outcome = sdk.outcome(state)
    if outcome is None:  # pragma: no cover - the loop only exits when finished
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
