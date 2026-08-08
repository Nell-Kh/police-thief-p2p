"""The end-of-game mutual audit: hashes first, then the physics.

Hash verification is the rulebook's iron law: recompute every revealed record
against its commitment; one mismatch is proven tampering and a total technical
loss. On top of that we re-verify the *trajectory* - something the reference
implementation never does: a log can be hash-consistent yet physically
impossible (teleports, diagonal moves, walks through declared barriers). Our
audit catches both, and the same engine powers the Replay Viewer's verdict.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..constants import MOVE_DELTAS
from ..shared.schema import GameContract
from .board import Cell
from .corroboration import verify_concession
from .crypto import audit_records
from .sealing import revealed_move
from .state_summary import revealed_cell, turn_payloads

__all__ = [
    "VERDICT_OK",
    "VERDICT_TAMPERED",
    "AuditReport",
    "audit_disclosure",
    "verify_concession",  # re-exported: the corroboration layer lives next door
    "verify_trajectory",
]

VERDICT_OK = "Verified OK"
VERDICT_TAMPERED = "TAMPERED"


@dataclass(frozen=True)
class AuditReport:
    """The outcome of auditing one side's disclosed log."""

    hashes_ok: bool
    physics_ok: bool
    verified_steps: list[Any]
    failed_steps: list[Any]
    violations: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """The audit passes only when both layers pass."""
        return self.hashes_ok and self.physics_ok

    @property
    def verdict(self) -> str:
        """The Replay Viewer's stamp for this log."""
        return VERDICT_OK if self.passed else VERDICT_TAMPERED


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


def audit_disclosure(
    disclosure: dict[str, Any],
    contract: GameContract,
    *,
    own_barriers: list[Cell] | None = None,
    conceded_at: Cell | None = None,
    answered_at: Cell | None = None,
) -> AuditReport:
    """Audit an opponent's full end-of-game disclosure.

    Args:
        disclosure: ``{"sender": role, "records": [...], "result_claim": ...}``.
        contract: the signed contract fixing the physics being verified.
        own_barriers: the stones *we* placed. Evidence we hold with certainty,
            so a self-declared capture can be corroborated without trusting the
            opponent's reveal. Omit it and that layer simply does not run.
        conceded_at: the cell the opponent named in its sealed concession, as we
            received it on the wire.
        answered_at: the cell we broadcast in our own ``capture_claim`` and the
            opponent answered ``caught: true`` to.
    """
    records = list(disclosure.get("records", []))
    hashes = audit_records(records)
    violations = verify_trajectory(records, contract, str(disclosure.get("sender", "")))
    violations += verify_concession(
        records,
        board_size=contract.board.grid_size,
        own_barriers=own_barriers,
        conceded_at=conceded_at,
        answered_at=answered_at,
    )
    return AuditReport(
        hashes_ok=bool(hashes["passed"]),
        physics_ok=not violations,
        verified_steps=list(hashes["verified_steps"]),
        failed_steps=list(hashes["failed_steps"]),
        violations=violations,
    )
