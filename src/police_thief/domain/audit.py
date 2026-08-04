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
from .crypto import audit_records
from .sealing import revealed_move, revealed_position

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


def _turn_payloads(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The revealed turn payloads, in step order."""
    turns = [
        record.get("payload", {})
        for record in records
        if record.get("payload", {}).get("type") == "turn"
    ]
    return sorted(turns, key=lambda payload: payload.get("step", 0))


def verify_trajectory(
    records: list[dict[str, Any]], contract: GameContract, role: str
) -> list[str]:
    """Physics violations in a revealed trajectory (empty list = clean).

    Checks: the declared start cell matches the signed contract, every step's
    move is a legal displacement (orthogonal or stay - a diagonal cannot even
    be expressed as a delta), every position stays on the board, and each
    consecutive position pair actually differs by the declared move.
    """
    violations: list[str] = []
    turns = _turn_payloads(records)
    if not turns:
        return violations
    size = contract.board.grid_size
    start = contract.board.cop_start if role == "police" else contract.board.thief_start
    previous = start
    for payload in turns:
        step = payload.get("step")
        try:
            position = revealed_position(payload)
            move = revealed_move(payload)
        except (KeyError, ValueError, TypeError):
            violations.append(f"step {step}: unreadable position or move")
            continue
        if not (0 <= position[0] < size and 0 <= position[1] < size):
            violations.append(f"step {step}: position {position} off the board")
        delta = MOVE_DELTAS.get(move)
        if delta is None:
            violations.append(f"step {step}: illegal move {move!r}")
        else:
            expected = (previous[0] + delta[0], previous[1] + delta[1])
            if position != expected:
                violations.append(
                    f"step {step}: declared {move} from {previous} but stood at {position}"
                )
        previous = position
    return violations


def audit_disclosure(
    disclosure: dict[str, Any], contract: GameContract
) -> AuditReport:
    """Audit an opponent's full end-of-game disclosure.

    Args:
        disclosure: ``{"sender": role, "records": [...], "result_claim": ...}``.
        contract: the signed contract fixing the physics being verified.
    """
    records = list(disclosure.get("records", []))
    hashes = audit_records(records)
    violations = verify_trajectory(records, contract, str(disclosure.get("sender", "")))
    return AuditReport(
        hashes_ok=bool(hashes["passed"]),
        physics_ok=not violations,
        verified_steps=list(hashes["verified_steps"]),
        failed_steps=list(hashes["failed_steps"]),
        violations=violations,
    )
