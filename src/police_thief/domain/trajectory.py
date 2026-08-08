"""Re-verifying a revealed trajectory against the physics the contract signed.

A log can be hash-consistent yet physically impossible - a teleport, a diagonal
step, a walk off the board, or a declared move that does not match the two cells
it connects. The reference implementation never checks this; we do, and the same
pass powers the Replay Viewer's verdict. It lives beside :mod:`audit`, which
calls it once the hashes have been re-verified.
"""

from __future__ import annotations

from typing import Any

from ..constants import MOVE_DELTAS
from ..shared.schema import GameContract
from .board import Cell
from .sealing import revealed_move
from .state_summary import revealed_cell, turn_payloads


def verify_trajectory(
    records: list[dict[str, Any]], contract: GameContract, role: str
) -> list[str]:
    """Physics violations in a revealed trajectory (empty list = clean).

    Checks: the declared start cell matches the signed contract, every step's
    move is a legal displacement (orthogonal or stay - a diagonal cannot even
    be expressed as a delta), every position stays on the board, and each
    consecutive position pair actually differs by the declared move.

    **It degrades rather than accusing.** A peer whose payloads reveal no cell
    at all is using a legal schema (kit SPEC §3: the payload schema is not an
    interop constraint), so the displacement check simply has no evidence to run
    on and is skipped for those steps. Treating our own payload schema as
    everyone's is precisely how a checker comes to call an honest, sealed,
    counted series *tampered* - the kit names that mistake and warns it "must
    not get a second home". The move itself is still checked whenever it is
    readable, because that needs no position.
    """
    violations: list[str] = []
    turns = turn_payloads(records)
    if not turns:
        return violations
    size = contract.board.grid_size
    start = contract.board.cop_start if role == "police" else contract.board.thief_start
    previous: Cell | None = start
    for payload in turns:
        step = payload.get("step")
        position = revealed_cell(payload)
        move = revealed_move(payload)
        delta = MOVE_DELTAS.get(move)
        if delta is None:
            violations.append(f"step {step}: illegal move {move!r}")
        if position is None:
            previous = None  # no cell revealed: nothing to chain the next step to
            continue
        if not (0 <= position[0] < size and 0 <= position[1] < size):
            violations.append(f"step {step}: position {position} off the board")
        if delta is not None and previous is not None:
            expected = (previous[0] + delta[0], previous[1] + delta[1])
            if position != expected:
                violations.append(
                    f"step {step}: declared {move} from {previous} but stood at {position}"
                )
        previous = position
    return violations
