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

from ..shared.schema import GameContract
from .board import Cell
from .corroboration import verify_concession
from .crypto import audit_records
from .trajectory import verify_trajectory

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


def _disclosed_records(disclosure: dict[str, Any]) -> list[dict[str, Any]] | None:
    """The records of a structurally sound disclosure, or None if it is malformed.

    A hostile or broken peer can send ``records`` as a string, a record as a
    bare number, or a payload that is not an object - each of which would crash
    a ``.get`` chain deep in verification. Structural soundness is checked once,
    here, so the audit can fail such a disclosure cleanly (the peer forfeits)
    instead of taking us down with it. This is a *structure* check only, never a
    schema one: which fields a payload object carries stays the peer's own
    business (kit SPEC §3), so any dict payload passes.
    """
    if not isinstance(disclosure, dict):
        return None
    raw = disclosure.get("records", [])
    if not isinstance(raw, list):
        return None
    for record in raw:
        if not isinstance(record, dict) or not isinstance(record.get("payload", {}), dict):
            return None
    return raw


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
    records = _disclosed_records(disclosure)
    if records is None:
        return AuditReport(
            hashes_ok=False, physics_ok=False, verified_steps=[], failed_steps=[],
            violations=["malformed disclosure: records must be a list of objects "
                        "with object payloads"],
        )
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
